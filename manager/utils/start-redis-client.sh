#!/bin/bash
# Script to start redis worker with the given URL string
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 10-may-2020

if [[ ! -v REDIS_URL ]] || [[ -z "$REDIS_URL" ]]; then
    CONNECT_STR="redis://locahost:6379"
else
    CONNECT_STR=${REDIS_URL}
fi

rq worker --url ${CONNECT_STR}

