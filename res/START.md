
# Bringing Up

Once the three computers are setup, the OOTB components have to be brought up. Follow the following steps.


### Starting REDIS Database

1. Start the `REDIS` server

```bash
sudo systemctl start redis
```

2. Check whether `REDIS` is up and running

```bash
sudo systemctl status redis
sudo netstat -lnp | grep redis
```

Other `REDIS` related useful commands are as follows.

```bash
sudo systemctl restart redis
sudo systemctl stop redis
```

Above commands used to restart or stop `REDIS`.



### Starting OOTB Django Components (front-end)

1. Run the OOTB (Django) front-end.

```bash
cd ops-on-the-bench/manager
python3 manage.py runserver 192.168.1.5:8000
```

The IP address is the address of the local computer (which is also given in the `ALLOWED_HOSTS`) and any preferable port (here 8000 is used).

2. The OOTB Django front-end has to be triggered to update status of running simulations regularlyi by callinfg a URL. To do that, a cron job must be started. A script is available to call this URL. The script is called `update-manager.sh`. Do the following to create the cron job.

  - Edit crontab by running,

   ```bash
   crontab -e
   ```

  - Insert the following entry in the Cron file. /.../ refers to where OOTB is installed.

  ```bash
  * * * * * /.../ops-on-the-bench/manager/update-manager.sh -i 192.168.1.5 -p 8000 
  ```

  The above `/.../` refers to where OOTB is installed.


### Starting OOTB Worker Components (back-end)

1. Start `ootb` instances, as many as required

```bash
docker run -d -i -v /home/myname/data:/opt/data -e "REDIS_URL=redis://:deadbeefdeadbeefdeadbeefdeadbeef@192.168.1.1:6379" -e "DJANGO_CONN=192.168.1.5:8000" --network="host" --name="ootbinstance01" ootb
```

The `/home/myname/data:/opt/data` maps an internal folder of the instance to the folder created in the previous step. The 2 environmental variables, `REDIS_URL` and `DJANGO_CONN` are used to specify the connectivity details for the `REDIS` database and the computer where Django is installed. The `ootb` at the end is the Docker image what was created in a previous step. 

The `ootbinstance01` is the name given to the instance. Depending on the resources available (i.e., disk space, RAM, CPU cores), any number of `ootb` instances can be created.

2. Check the created and running instances by using the following command.

```bash
docker ps -a
```

A list is output that shows the `ootb` images currently instantiated and information about each instance.

