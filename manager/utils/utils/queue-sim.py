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

def main():

    # make string of the omnetpp.ini file
    with open ('omnetpp.ini', 'r') as inifilefp:
        inistr = inifilefp.read()

    # make the parameters
    execution = 1
    arguments = {
                'user' : 'adu',
                'title' : 'Epidemic with SWIM mobility',
                'omnetpp.ini' : inistr,
                'runconfig' : 'General'
                'summarizing_precision' : 100.0
                }

    # connect to REDIS
    redisconn = redis.Redis(host='localhost')
    queue = rq.Queue(connection=redisconn)

    # queue the simulation
    queue.enqueue(worker.run_simulation, execution, arguments, job_timeout=43200)


if __name__ == "__main__":
    main()

