#!/bin/bash
# Script to perform initial work and start redis worker
# with the given URL string.
#
# Author: Asanga Udugama (adu@comnets.uni-bremen.de)
# Date: 04-jan-2021

# Download and expand traces
OPT_FOLDER="/opt"
TRACES_ARCHIVE="ootb-traces.tar.gz"
TRACES_LINK="https://seafile.zfn.uni-bremen.de/f/291602b767e642d49827/?dl=1"

echo "About to download and expand traces into $OPT_FOLDER."
echo "Downloading..."
wget -q "$TRACES_LINK" -O "$TRACES_ARCHIVE"
echo "Download completed. Expanding ..."
tar -xzf "$TRACES_ARCHIVE" -C "$OPT_FOLDER"
rm "$TRACES_ARCHIVE"
echo "All traces downloaded and expanded."

# Start redis
echo "Starting REDIS client"
if [[ ! -v REDIS_URL ]] || [[ -z "$REDIS_URL" ]]; then
    CONNECT_STR="redis://locahost:6379"
else
    CONNECT_STR=${REDIS_URL}
fi

echo "Worker ready to execute OPS simulation jobs."

rq worker --url ${CONNECT_STR}
