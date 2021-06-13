Build image
===========

`docker build -t ootb .`

Start docker
============

`docker run -i -v <local path>:<image path> -e "REDIS_URL=redis://:<redis db password>@<redis db server>:6379" --network="host" --name <image name> ootb`

Stop docker
===========

`docker stop <image name>`

Remove image
============

`docker rm <image name>`
