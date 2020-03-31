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


Misc
====

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
