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

A basic test worker can be found here: `manager/utils/worker.py`.

To use this inside a docker image, it should be sufficient to copy the utils
directory to the image and start the worker by calling `worker.py` directly.


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
