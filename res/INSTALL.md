 
# Building and Installing

The deployment architecture of OOTB is shown in the following picture.

<p align="center">
<img src="res/pics/ootb-deployment.png" alt="OOTB Deployment Architecture" width="500"/>
</p>

The picture shows three parts of the deployment that have to be setup.

- Setup front-end
- Setup `REDIS` database
- Setup back-end

In the explanations below, we assume that the three parts are deplyed in three different Linux based computers (servers) with connectivity to each other. But, they may also be in one single computer.

The OOTB platform is realized using the Python programmimg language. Therefore, for developing, setting up and finally, brining up the OOTB platform, Python must be available in all computers. All components have been tested on **Python 3**.


### Setup REDIS Database




1. Install `Python` in a `Linux` based computer with network connectivity.

  - `Python 3.6.9`
  - `Ubuntu 18.04.6 LTS`

2. Install `REDIS` packages in `Linux`

```bash
sudo apt update
sudo apt install redis-server
```

3. Create a passphrase for the `REDIS` database which is used to access the database by other users (e.g. Django)

```bash
python3 -c 'import secrets; print(secrets.token_hex(16))'
```

4. Setup `REDIS` configuration by editing the file `/etc/redis/redis.conf`. The following entries must be modified.

```bash
bind 192.168.1.1 127.0.0.1
port 6379
requirepass deadbeefdeadbeefdeadbeefdeadbeef
```

The `bind` entry specifies the IP address of the network interface of the computer (on which `REDIS` is run), waiting for incomming connections. `port` specifies the IP port on which `REDIS` is listening (6379 is the standard port). Use the passphrase output in previous step for `requirepass`. 


### Setup OOTB Django Components (front-end)

1. Install `Python` in a `Linux` based computer with network connectivity.

  - `Python 3.6.9`
  - `Ubuntu 18.04.6 LTS`

2. Create and activate a `virtual environment` of `Python`

```
python3 -m venv venv
. ./venv/bin/activate
```

3. Open a terminal and pull the OOTB repository (this repository) from Github

```
git clone https://github.com/ComNets-Bremen/ops-on-the-bench.git
```

4. Install all the packages specified in `requirements.txt` using `pip` package manager of `Python`. You may have to update `pip` before you use.

```
pip install --upgrade pip
pip install -r requirements.txt
```

5. Configure the settings of Django with the parameter values to for this installation. There are three areas that is usually set for OOTB.

The changes should not be done in the `settings.py` in the `manager/manager` folder directly. Please create a new file in `manager/manager` with the name `local_settings.py` next to it. In here, all settings can be overwritten. The `local_settings.py` will be private to you and will not be submitted to the repository to keep your credentials private.

- Create a secret key on the terminal.

```bash
python3 -c 'import secrets; print(secrets.token_hex(16))'
```

- Input the printed token as the `SECRET_KEY` as shown below, placing the example.

```bash
SECRET_KEY = 'deadbeefbeefdeaddeadbeefbeefdead'
```

- Give the host on which Django is setup (i.e. the current computer) with the `ALLOWED_HOSTS` key word.

```bash
ALLOWED_HOSTS = [
        '127.0.0.1',
        '::1',
        'localhost',
        '192.168.1.0/16',
        '192.168.1.5'
        ]
```

- Give connection details of `REDIS` (remember the quotation marks around values)

```bash
REDIS_DB_HOST       = '192.168.1.1'
REDIS_DB_PORT       = 6379
REDIS_DB_PASSWORD   = 'deadbeefdeadbeefdeadbeefdeadbeef'
```

- Give details of the SMTP server used to send emails. A Google mail based simple (less secure) solution is shown here, but an own SMTP server may also be used.

```bash
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'ob2022@gmail.com'
EMAIL_HOST_PASSWORD = 'deadbeefdeadbeef'
DEFAULT_SENDER_MAIL_ADDRESS = "ob2022@gmail.com"
```
When using Google's mail service, an application must be created with the credentials which are then used here. See [link](https://data-flair.training/blogs/django-send-email/) for more info.

Another is to setup your own SMTP server. In that case, setup your SMTP server and provide only the following details.

```bash
DEFAULT_SENDER_MAIL_ADDRESS = 'ootb-admin@deadbeef-domain.de'
DEFAULT_RECEIVER_MAIL_ADDRESS = DEFAULT_SENDER_MAIL_ADDRESS
```


6. OOTB definitions  are in a local SQLite database and this database is created by importing the `db.json` file. Follow the steps below to create the database.

```bash
cd ops-on-the-bench/manager
python3 manage.py makemigrations
python3 manage.py migrate
python3 manage.py loaddata db.json
```

7. Create a administrative user (super user) in Django

```bash
cd ops-on-the-bench/manager
python3 manage.py createsuperuser
```



### Setup OOTB Worker Components (back-end)

1. Install `Python` in a `Linux` based computer with network connectivity.

  - `Python 3.7.3`
  - `Debian GNU/Linux 10 (buster)`

2. Open a terminal and pull the OOTB repository (this repository) from Github

```
git clone https://github.com/ComNets-Bremen/ops-on-the-bench.git
```

3. Install Docker system on the selected Linux distribution (`Debian GNU/Linux 10 (buster)` recommended above). Use the [link](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-debian-10) on installing Docker. Follow the procedure given in the link and also setup `Executing the Docker Command Without Sudo`.

4. Create the OOTB Docker image.

```bash
cd ops-on-the-bench/manager/utils
docker build . -t ootb
```

The above command will use the `Dockerfile` in the `utils` folder. This process takes a long time to make the image. Check whether the image is created using the following command.

```bash
docker images
```

The output should show a list of entries of one is `ootb`.

5. The output of simulations are stored in a common place. Create a folder for this purpose.

```bash
mkdir /home/myname/data
```

