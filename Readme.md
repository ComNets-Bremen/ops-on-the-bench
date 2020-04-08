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
```

worker
------

The code related to the worker side of things can be found in thwe following
folders.

- `docker` - contains the Docker file to build the Ubuntu 16.04 based OPS
image and the related scripts run inside the image

- `utils` - contains the utility that brings up and tears down workers that
perform the simulations

The `ootb-ctl.py` in `utils` folder is a command line utility to bring up workers
and to instantiate Docker container to server those worker. The command line
syntax is as follows.

- start a deamonized worker and bring up an instance of the OPS docker image, specifying
where the output is placed
```
ootb-ctl.py -m new -r 10.10.160.103 -d /home/adu/datafolder
``` 
 
- show all the currently active workers
```
otb-ctl.py -m list -r 10.10.160.103
```

- tear down an active deamonized worker identified by an ID, brining down also the docker 
container simultaneously
```
ootb-ctl.py -m stop -r 10.10.160.103 -i DD42F428C7

- check the operation of the active workers by submitting jobs with an `omnetpp.ini`
```
otb-ctl.py -m test -r 10.10.160.103 -c ./omnetpp.ini
```





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
