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
pip3 install dropbox
pip3 install slugify
```
Please be aware that the manager requires a working mail configuration on the server. Either you setup a nullclient or you configure the email backend correctly: as described [here](https://docs.djangoproject.com/en/dev/topics/email/#smtp-backend).

worker
------

Here are the worker side details. The code related to the worker is available in the 
`manager/utils` folder.

- The code and other files that implement the worker

  - `worker.py` - implements the worker called through the REDIS queue which calls other functions (in `opsrun.py`)

  - `opsrun.py` - implements the functions that run simulations and process results

  - `worker_utils.py` - implements the some helper functions required by other functions

  - `dropboxops.py` - implements all operations related to uploading results to a DropBox account

  - `Docker` - spec to create the OPS based Docker image

  - `stat-list.txt` - contains the details of each stat used in the results processing

  - `net-list.txt` - contains the details of all the network names possible to be simulated which are required when extracting results using the `scavetool`

  - `queue-sim.py` and `omnetpp.ini` are to run test simulations without the Django front-end

- Dependancies
```bash
pip3 install matplotlib
pip3 install fpdf
pip3 install dropbox
```

- Command for building OPS Docker image
```bash
docker build . -t ootb
```

- Command for bringning up OPS Docker image
```bash
docker run -i -d -v /home/data:/opt/data -e "REDIS_URL=redis://:password@192.168.0.1:6379" --network="host" ootb
```

`/home/data` is a folder in the host machine which is mounted as `/opt/data` inside 
the `ootb` Docker container, the `-d` option brings up the container detached,
`--network` says the networking environment of the container is the same as the 
host's and `-e REDIS_URL=redis://:password@192.168.0.1:6379` specifies the connecting
password, the IP address and the hosted port of the server on which the REDIS job queue 
is located 

- When each simulation is run, a (unique) folder is created in the mounted folder ('/home/data' 
from above example) using the job ID. There are files and sub-folders inside this 
job folder. Here are the details.

  - `orig-omnetpp.ini` is the original OMNeT configuration file sent by Django
  - `omnetpp.ini` is the sanitized and actually used OMNeT configuration file in simulation
  - `General-0.sca` is the scalar file created during the simulation
  - `General-0.vec` is the vector file created during the simulation
  - `General-0.vci` is the vector index file created during the simulation
  - `ops.log` is the activity log created by OPS
  - `graphs` is the folder that contains all the scalar results and vector results (graphs) as .pdf files
  - `csv` is the folder that contains the precision-changed .csv files (currently set to 100 seconds) 
  - `simrun` is the folder that contains data about the simulation run (e.g., simulation duration, events, etc.)
  - `temp` is the folder where temporary files are stored 
  - `INFO.txt` contains info on the files and folders included in the archive sent to user

- When the simulation is completed, a selected set of files and folders are zipped and sent to the remote file
sharing service configured (e.g., DropBox), and currently `omnetpp.ini`, `INFO.txt`, `graphs` folder,
`csv` folder and the `simrun` folder are included in this zip file

- When OPS Docker image is run attached (without `-d`), it creates a container that shows the operation 
of the worker and errors (where there are) on the command-line (useful for troubleshooting)
```bash
docker run -i -v /home/data:/opt/data -e "REDIS_URL=redis://:password@192.168.0.1:6379" --network="host" ootb
```

- To login to a running container to troubleshoot (`abcd` is the container name)
```bash
docker exec -i -t abcd /bin/bash
```

- Once the zip file is made and uploaded to the file sharing service, all files related to the simulation are 
removed

- The worker code sends the status of the activities periodically (every 3 seconds) using the `meta` dictionary of the job.

  - `current_state` - what activity is the worker in currently (INITILIZING, SIMULATING, PARSING, ARCHIVING, UPLOADING, TERMINATING, COMPLETED, CRASHED)
  - `start_time_str` - starting time of the work
  - `peak_disk_usage` - peak disk space used by all programs (simulation, results parsing, etc) 
  - `peak_sim_ram_usage` - peak RAM used duriung the simulation
  - `peak_results_ram_usage` - peak RAM used when parsing results
  - `sim_completed_perc` - percentage completion of the simulation itself
  - `results_completed_perc` - percentage completion of results parsing (this only an estimation)
  - `shared_link` - link to the Dropbox zip file containing the job output


- To test workers independent from the Django front-end, follow the following procedure
  - setip a local Redis instance (127.0.0.1, with password)
  - create an `omnetpp.ini` file to run
  - update the parameters in the file config file `queue-sim-config.cfg`
  - run command 
    ```bash
    ./queue-sim.py -c queue-sim-config.cfg
    ```


Storage backend
===============

The following information are transferred to the worker for handling the result
data:

- `storage_backend_id`: An identifier for the upload service like `dropbox` or
  `local`. Has to be implemented on the worker. One should check this variable
  on the worker side to select the upload method.

- `storage_backend`: A descriptive name of the backend like "Dropbox account of
  abc"

- `storage_backend_token`: The token required for the backend

Loading Data
===============

To Load OOTB definitions/models data into empty DB.

The dumped data is saved as `db.json` and it contains all omnetpp configurations inputted.
Process is automated by running bash script: `dump.sh`

To use the script, cd to the project directory and run the following command:
`./dumb.sh`
The script runs: makemigrations, migration and loaddata commands.

The script carries out the following steps:
- make migrations: `python manage.py makemigrations`
- migrate on the emoty DB: `python manage.py migrate`
- load the dumped data: `python manage.py loaddata db.json`


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
- Plik as a temporary file transfer service? https://github.com/root-gg/plik
- ...

Accessing Server Configurations
-------------------------------

The manager offers a simple key-value system for server (and simulation
independent) data. This Server configurations can be accessed in two ways:

- Accessing `/omnetppManager/get-server-config/` as a logged in user returns a
  json object containing all configured server configurations. This is mainly
  meant for debugging.
- Accessing `/omnetppManager/get-server-config/` with the two HTTP-headers
  `HTTP-X-HEADER-TOKEN` and `HTTP-X-HEADER-SERVER-ID` set will return the
  values as json for the given server only.

This can be tested using `curl`:
    curl -H "HTTP-X-HEADER-SERVER-ID: <SERVER_ID>" -H "HTTP-X-HEADER-TOKEN: <TOKEN>" <SERVER_ADDRESS>/omnetppManager/get-server-config/

Token and server ID are configured in the table `Server Config`, the
key-value-pairs in `Server Config Values`.

