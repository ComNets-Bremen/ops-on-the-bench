#!/usr/bin/env python3
#
# Script to control the environment of setting up and 
# tearing down workers to run OPS simulations.
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 03-April-2020
#
import daemon
import datetime
import argparse
import os
import sys
import redis
import psutil
import rq
import uuid
import time
import subprocess
import shutil


REDISPORT = 6379
REDISDBID = 5
HASHNAME = 'opsworkers'
ENCODING = 'utf-8'
WORKERIDLEN = 8
LOGPREFIX = 'worker-'

def run_simulation(arguments):
    
    # log details
    print('%s got a simulation to run: %s %s %s \n' % (datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S'), \
                                                                arguments['user'], arguments['title'], \
                                                                arguments['runconfig']))

    # get worker ID
    workerid = os.environ['OOTB_WORKER_ID']

    # create job folder
    job = rq.get_current_job()
    cwd = os.getcwd()
    jobfolder = os.path.join(cwd, str(job.get_id()))
    os.mkdir(jobfolder)

    # create the omnetpp.ini from arguments in job folder
    inipath = os.path.join(jobfolder, 'omnetpp.ini')
    with open(inipath, 'w') as inifp:
        inifp.write(arguments['omnetpp.ini'])

    # run simulation
    bashcmd = '/opt/OPS/simulations/ops-run.sh %s %d' % (str(job.id), 100)
    subprocess.call(['docker', 'exec', workerid, '/bin/bash', '-c', bashcmd])

    # completed
    print('Simulation completed. Results are located at ', jobfolder)


def new_worker(redishost, port, datafolder):
    print('start new worker')
    
    # get a unique ID for the worker
    workerid = 'DD' + uuid.uuid4().hex[:WORKERIDLEN].upper()
    
    # create folder to hold output of all simulations run in container 
    ownfolder = os.path.join(datafolder, workerid)
    os.mkdir(ownfolder)

    # bring up the container
    foldermapping = ('%s:/opt/data' % (ownfolder))
    subprocess.call(['docker', 'run', '-i', '-d', '-v', foldermapping, '--name', workerid, 'ootb', '/bin/bash'])

    # update OPS worker info in REDIS
    redisconn = redis.Redis(host=redishost, port=port, db=REDISDBID)
    redisconn.hset(HASHNAME, workerid, '0')

    # create the worker log
    logpath = os.path.join(ownfolder, (LOGPREFIX + workerid + '.log'))
    os.umask(0)
    logfp = open(os.open(logpath, os.O_CREAT | os.O_WRONLY, 0o777), 'w')

    # worker setup message
    print('OPS container and worker daemon started with ID', workerid)

    # daemonize the process
    damomize = daemon.DaemonContext(working_directory=ownfolder, detach_process=True, stdout=logfp, stderr=logfp)
    damomize.open()

    # get PID and update REDIS
    pidstr = str(os.getpid())
    print('PID from daemon', pidstr)
    redisconn = redis.Redis(host=redishost, port=REDISPORT, db=REDISDBID)
    redisconn.hset(HASHNAME, workerid, pidstr)
    
    os.environ['OOTB_WORKER_ID'] = workerid
    
    # start REDIS queue handler
    listen = ['high', 'default', 'low']
    redisconn = redis.Redis(host=redishost, port=REDISPORT)
    with rq.Connection(redisconn):
        worker = rq.Worker(map(rq.Queue, listen))
        worker.work()


def stop_worker(redishost, port, workerid):
        
    # get all workerinfo from REDIS
    redisconn = redis.Redis(host=redishost, port=port, db=REDISDBID)
    allworkers = redisconn.hgetall(HASHNAME)
    
    # iterate thru allworkers and find the process ID
    pidstr = None
    if allworkers == None:
        print('No workers currently active')
    else:
        for key, value in allworkers.items():
            if key.decode(ENCODING) == workerid:
                pidstr = value.decode(ENCODING)
                break

    # kill the worker
    if pidstr:
        pid = int(pidstr)
        p = psutil.Process(pid)
        p.kill() # or terminate()
        redisconn.hdel(HASHNAME, workerid)

        # stop the container and remove from list (doesn't remove image)
        subprocess.call(['docker', 'stop', workerid])
        subprocess.call(['docker', 'rm', workerid])

        print('Worker with Worker ID', workerid, 'stopped')        
    else:
        print('Worker with Worker ID', workerid, 'not found')

def list_workers(redishost, port):

    # get all workerinfo from REDIS
    redisconn = redis.Redis(host=redishost, port=port, db=REDISDBID)
    allworkers = redisconn.hgetall(HASHNAME)

    # show all workerinfo
    if allworkers == None or not allworkers:
        print('No workers currently active')
    else:
        print('List of Current Workers')
        print('Worker ID ', 'Process ID')
        for key, value in allworkers.items():
            print(key.decode(ENCODING).ljust(12, ' '), value.decode(ENCODING))

def test_job(redishost, port, conf):

    # make string of the omnetpp.ini file
    with open (conf, 'r') as inifilefp:
        inistr = inifilefp.read()

    # make the parameters
    arguments = {
                'user' : 'adu',
                'title' : 'Epidemic with SWIM mobility',
                'omnetpp.ini' : inistr,
                'runconfig' : 'General'
                }

    # connect to REDIS
    redisconn = redis.Redis(host=redishost, port=port)
    queue = rq.Queue(connection=redisconn)

    # queue the simulation
    queue.enqueue('ootb-ctl.run_simulation', arguments)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', type=str, help='Operation model - new, stop, list, test', required=True)
    parser.add_argument('-r', '--redishost', type=str, help='REDIS host, e.g., 192.168.12.12', required=True)
    parser.add_argument('-p', '--port', type=int, help=('REDIS port, e.g., %d' % (REDISPORT)), default=REDISPORT)
    parser.add_argument('-i', '--id', type=str, help='OPS Worker ID to stop', default=None)
    parser.add_argument('-c', '--conf', type=str, help='The omnetpp.ini file to use with test', default='omnetpp.ini')
    parser.add_argument('-d', '--datafolder', type=str, help='The default folder where output must be created', default='./')
    args = parser.parse_args()

    if args.mode == 'new':
        new_worker(args.redishost, args.port, args.datafolder)
    elif args.mode == 'stop':
        stop_worker(args.redishost, args.port, args.id)
    elif args.mode == 'list':
        list_workers(args.redishost, args.port)
    elif args.mode == 'test':
        test_job(args.redishost, args.port, args.conf)

if __name__ == "__main__":
    main()

