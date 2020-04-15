#!/usr/bin/env python3

# Example worker script:
#
# Can be
# a) imported into django: django uses run_simulation to start the simulation
# b) run inside a container to handle the jobs
#

import subprocess
import os
import sys
import shutil
import socket
import traceback
import opsrun

# We have different import paths depending on the module import via django
# or the direct calling as an app
if __name__ == "__main__":
    import worker_utils
else:
    import utils.worker_utils

from rq import get_current_job, Connection, Worker

import time

from enum import Enum

## Definition of the run binary / executable
class SimulationRuntimes(Enum):
    OPS_EPIDEMIC = 1
    OPS_KEETCHI = 2

def run_simulation(executable, arguments):
    job = get_current_job()
    if job: # in worker environment:
        print("Processing job", job.id)
        job.meta["handled_by"] = socket.gethostname()
        job.meta["exception"] = None
        job.save_meta()

    try:
        ### start the simulation here!
        print("Executable", executable)
        if executable == SimulationRuntimes.OPS_EPIDEMIC:
            print("Epidemic simulation")
        elif executable == SimulationRuntimes.OPS_KEETCHI:
            print("Keetchi simulation")

        print("Arguments:")
        for arg in arguments:
    #        print(arg, arguments[arg])
            print(arg)
        # time.sleep(10)
        opsrun.run_ops(str(job.get_id()), arguments)

        print(job.id)
        print(job.meta)

#        raise Exception("Fail!") # test failed job

        ### end simulation processing
    except:
        # Any exception caused? -> store it in the meta data so we can access
        # it later on to help the user to debug the parameters / simulation
        if job: # worker environment?
            job.meta["exception"] = traceback.format_exc()
            job.save_meta()
        raise # Throw exception again

    return {
            "errors"  : [], # simulation errors?
            "results" : [], # simulation results?
            }


if __name__ == '__main__':
    # make imports running for worker and for django
    BASE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, BASE_PATH)

#    print(os.path.abspath(os.path.dirname(__file__)))
#    run_simulation(SimulationRuntimes.OPS_EPIDEMIC, {"a" : "b"})
    with Connection():
        queue_name = sys.argv[1:] or ["default"]
        w = Worker(queue_name)
        w.work()
