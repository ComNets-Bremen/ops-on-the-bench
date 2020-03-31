#!/usr/bin/env python3

import subprocess
import os
import shutil
#import utils

import time

from enum import Enum

class SimulationRuntimes(Enum):
    OPS_EPIDEMIC = 1
    OPS_KEETCHI = 2

def run_simulation(executable, arguments):
    print("Executable", executable)
    print("Arguments:")
    for arg in arguments:
        print(arg, arguments[arg])
    time.sleep(10)

    return {
            "errors" : [],
            "results" : [],
            }


if __name__ == '__main__':
    run_simulation(SimulationRuntimes.OPS_EPIDEMIC, {"a" : "b"})
