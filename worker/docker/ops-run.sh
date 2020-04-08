#!/bin/bash

JOBFOLDER="$1"
RESULTSRESSEC="$2"

# remove the results folder soft link of any previous simulations
if [ -e "/opt/OPS/simulations/results" ]; then
	rm /opt/OPS/simulations/results
	echo "Existing link to /opt/OPS/simulations/results folder removed"
fi

# remove the soft link to the omnetpp.ini file
if [ -e "/opt/OPS/simulations/omnetpp.ini" ]; then
	rm /opt/OPS/simulations/omnetpp.ini
	echo "Existing link to /opt/OPS/simulations/omnetpp.ini removed"
fi

# make new results folder soft link
ln -s /opt/data/$JOBFOLDER /opt/OPS/simulations/results
echo "setting results folder to /opt/data/$JOBFOLDER"

# make soft link to omnetpp.ini
ln -s /opt/data/$JOBFOLDER/omnetpp.ini /opt/OPS/simulations/omnetpp.ini
echo "setting omnetpp.ini to /opt/data/$JOBFOLDER/omnetpp.ini"

# run simulations
echo "starting the simulation"
ops-simu -r 0 -m -u Cmdenv -n .:../src:../modules/inet/src:../modules/KeetchiLib/src \
	--image-path=../modules/inet/images -l INET -l keetchi omnetpp.ini

# create graphs and other files
echo "creating graphs and resolution changed data"


