#!/usr/bin/env python3
#
# Queue a simulation.
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 12-April-2020
#
import redis
import rq
import worker
import argparse

def main(inifile, runconfig):

    # make string of the omnetpp.ini file
    with open (inifile, 'r') as inifilefp:
        inistr = inifilefp.read()

    # make the parameters
    execution = 1
    arguments = {
                'user' : 'adu',
                'title' : 'Epidemic with SWIM mobility',
                'omnetpp.ini' : inistr,
                'runconfig' : runconfig,
                'summarizing_precision' : 100.0,
                'storage_backend_id' : 'dropbox',
                'storage_backend_token' : '68xuOnr4c-AAAAAAAAAAIG1w-UhkxyhddCb9Hu011bedIpjsDwaO0Iujk4XPtcx_'
                }

    # connect to REDIS
    redisconn = redis.Redis(host='localhost')
    queue = rq.Queue(connection=redisconn)

    # queue the simulation
    queue.enqueue(worker.run_simulation, execution, arguments, job_timeout=259200)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--inifile', help='.ini file to use', required=True)
    parser.add_argument('-r', '--runconfig', help='Config tag to use', required=True)
    args = parser.parse_args()

    main(args.inifile, args.runconfig)

