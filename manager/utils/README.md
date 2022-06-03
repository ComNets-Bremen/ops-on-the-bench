Build docker image
==================

```bash
docker build -t ootb .
```

Check images
============

```bash
docker images
```


Start docker instance from image
================================
	
```bash
docker run -d -i -v <local path>:<image path> -e "REDIS_URL=redis://:<redis db password>@<redis db server>:6379" -e "DJANGO_CONN=<django server>:8000" --network="host" --name="<instance name>" ootb
```

Check running instances
=======================

```bash
docker ps -a
```


Stop docker instance
====================

```bash
docker stop <instance name>
```

Remove image
============

```bash
docker rm <image name>
```
