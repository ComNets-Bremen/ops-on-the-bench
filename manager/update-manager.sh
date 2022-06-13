#!/bin/bash
#
# Bash script to call the link to update status of running
# simulations in the front-end. This script has to be run
# regularly, so call it as a cron job. Since the lowest
# frequency of call is a minute in cron jobs, this script
# when called, can be made to run multiple times in a 
# minute.
#
# Command line syntax:
#   ./update-manager.sh -i ip -p port -m dur -f freq
#
# ip - IP address of server (where ootb runs)
# port - IP port of the server
# dur - set to 60, because lowest cron is a minute
# freq - when to call with the minute
# 
# How to make it a cron job:
# 1. Decide the above parameters (at least ip and port)
#
# 2. Run crontab -e on command line and insert
#    the following line
#
#    * * * * * /path-to-this-script/update-manager.sh -i 127.0.0.1 -p 8000
#
#    The 5 asterisks say run the given script every
#    minute continuously
#
# The number of times to call within a minute is computed by,
#   TIMES_TO_RUN = dur / freq
#
# @author: Asanga Udugama
# @date: 2022.05.25
#

# default values
IPADDRESS=10.10.160.110
IPPORT=8000
MAX_DURATION_SEC=60
RUN_FREQUENCY_SEC=2

# accept parameters
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -i|--target) IPADDRESS="$2"; shift ;;
        -p|--target) IPPORT="$2"; shift ;;
        -m|--target) MAX_DURATION_SEC="$2"; shift ;;
        -f|--target) RUN_FREQUENCY_SEC="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

# compute times to run
TIMES_TO_RUN=$(( $MAX_DURATION_SEC / $RUN_FREQUENCY_SEC ))
TIMES_RUN=0

while [ $TIMES_RUN -lt $TIMES_TO_RUN ]
  do
    # echo $TIMES_RUN
    wget -o /dev/null http://$IPADDRESS:$IPPORT/omnetppManager/manage_queues/
    TIMES_RUN=$(( $TIMES_RUN + 1 ))
    sleep $RUN_FREQUENCY_SEC
  done

