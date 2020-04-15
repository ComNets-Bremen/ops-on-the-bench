OPS on the bench repository
===========================

manager
-------

A simple job manager for omnetpp. Requires a venv with some requirements to
run:

- Create venv `python3 -m venv venv`

- Activate venv `. ./venv/bin/activate`

- Add dependencies:
```
pip3 install django
pip3 install rq
pip3 install django-formtools
pip3 install matplotlib
pip3 install fpdf
```

worker
------

Here are the worker side details. The code related to the worker is available in the 
`manager/utils` folder.

- `opsrun.py` - implements the functions that run simulations and process results

- `Docker` - spec to create the OPS based Docker image

- `stat-list.txt` - contains the details of each stat used in the results processing

- `queue-sim.py` and `omnetpp.ini` are to run test simulations without the Django front-end

- Dependancies
```bash
pip3 install matplotlib
pip3 install fpdf
```

- Command for building OPS Docker image
```bash
docker build . -t ootb
```

- Command for bringning up OPS Docker image
```bash
docker run -i -d -v /home/data:/opt/data --network="host" ootb
```

`/home/data` is a folder in the host machine which is mounted as `/opt/data` inside 
the `ootb` Docker container, the `-d` option brings up the container detached and 
`--network` says the networking environment of the container is the same as the 
host's 

- When each simulation is run, a (unique) folder is created in the mounted folder ('/home/data' 
from above example) using the job ID. There are files and sub-folders inside this 
job folder. Here are the details.

  - `omnetpp.ini` is the used OMNeT configuration file
  - `omnetpp.ini-General-0.sca` is the scalar file created during the simulation
  - `omnetpp.ini-General-0.vec` is the vector file created during the simulation
  - `omnetpp.ini-General-0.vci` is the vector index file created during the simulation
  - `ops.log` is the activity log created by OPS
  - `graphs` is the folder that contains all the results and graphs as .pdf files
  - `csv` is the folder that contains the precision-changed .csv files 
  - `temp` is the folder where temporary files are stored (currently not removed)


Misc
====

crontab
-------

Add the following line to your crontab to collect the simulation status
regularly:

`* * * * * wget -q -O /dev/null http://127.0.0.1:8888/omnetppManager/manage_queues/`

Tests
-----

Tested with

- Debian testing
- Python 3.7
- Django 3.0


Deployment
----------
For a real productive deployment, the following should be done:

- change the secure key in the `settings.py`
- username / password for redis?
- setup mail for notification
- setup a revserse proxy?
- fail2ban?
- ...

Ideas
-----

- Use magic wormhole to transfer the result? https://github.com/warner/magic-wormhole
- ...
