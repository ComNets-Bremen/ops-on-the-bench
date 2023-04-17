#!/usr/bin/env python3
#
# Queue a simulation. Use the given sample configuration as
# parameter file.
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 12-April-2020
#
import redis
import rq
import worker
import argparse

def main(configfile):
    # init valiables
    params = {}

    # read config and get parameters
    with open(configfile) as f:
        for line in f:
            if len(line.strip()) == 0 or line.strip().startswith('#'):
                continue
            cols = line.split('%%%')
            if cols[1].strip() == 'string':
                params[cols[0].strip()] = cols[2].strip()
            elif cols[1].strip() == 'int':
                params[cols[0].strip()] = int(cols[2].strip())
            elif cols[1].strip() == 'float':
                params[cols[0].strip()] = float(cols[2].strip())

    # make string of the omnetpp.ini file
    with open (params['inifile'], 'r') as inifilefp:
        inistr = inifilefp.read()

    # make the parameters
    execution = 1
    arguments = {
                'user' : params['user'],
                'title' : params['title'],
                'omnetpp.ini' : inistr,
                'runconfig' : params['runconfig'],
                'summarizing_precision' : params['precision'],
                'storage_backend_id' : params['backend'],
                'storage_backend_token' : params['backendtoken']
                }

    # connect to REDIS
    redisconn = redis.Redis(host=params['redishost'], port=params['redisport'], password=params['redispwd'])
    queue = rq.Queue(connection=redisconn)

    # queue the simulation
    queue.enqueue(worker.run_simulation, execution, arguments, job_timeout=params['jobtimeout'])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--configfile', help='configuration file with all the parameters', required=True)
    args = parser.parse_args()

    main(args.configfile)

