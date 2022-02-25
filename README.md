# OPS on the Bench (OOTB)


Research in Opportunistic Networks (OppNets) related to large scale evaluations depends on simulations to compare the performance of different forwarding protocols and their parameters ([1](https://www.mdpi.com/1999-5903/11/5/113)). The comparability and credibility of research are in crisis due to the variety of ways researchers perform evaluations ([2](https://dl.acm.org/doi/10.1145/1096166.1096174), [3](https://dl.acm.org/doi/10.1145/2812803), [4](https://www.acm.org/publications/policies/artifact-review-and-badging-current), [5](https://drops.dagstuhl.de/opus/frontdoor.php?source_opus=10347)). The code in this repository implements a simulation platform called **OPS on the Bench**(OOTB) to overcome these problems by enabling the use of OppNets benchmarks that foster repeatability, reproducibility and replicability of comparable, credible and scalable performance evaluations. More details about are vailable in the publication [Benchmarking data dissemination protocols for opportunistic networks](https://dl.acm.org/doi/10.1145/3458473.3458819)

The sections below describe installing, bringing up and using this platform. Here are the pointers to the different sections.

- Architecture of OOTB and required components - [Architecture and Prerequisites](#architecture-and-prerequisites)  
- Building up the OOTB platform - [Building and Installing](#building-and-installing)
- Bringing up the OOTB platform - [Bringing Up](#bringing-up)
- Running simulations in OOTB (by Users) - [Running Simulations](#running-simulations)
- 



##  Architecture and Prerequisites

The architecture of the OOTB platform consist of a set of vertical layers of sofware interacting to provide simulations of opportunistic networks. The picture below shows these components and the connections. 

To enable OOTB, the following software components are used.

- Django, a python-based web framework [Django](https://www.djangoproject.com)
- Docker, an OS-level virtualization environment [Docker](https://www.docker.com)
- Redis, a distributed in-memort data store [redis](https://redis.io)
- OPS, an opportunistic networking model framework [OPS](https://github.com/ComNets-Bremen/OPS.git)

The OOTB platform is realized using the Python programmimg language. Therefore, for developing, setting up and finally, brining up the OOTB platform, Python must be available in all computers. All components have been tested on **Python 3**.


## Building and Installing

The setup procedure of OOTB has two independent parts - setup of the Django components and setup of the Docker based workers. The complete OOTB platform can be setup on one computer running the Linux operating system. But for clarity, we setup these two independent parts in two separate Linux based computers.


### Setup OOTB Django Components


1. Install `Python` in a `Linux` bassed computer with a network connectivity.

  - `Python 3`
  - `Ubuntu LTS 10.4`

2. Create and activate a `virtual environment` of `Python`

```
python3 -m venv venv

./venv/bin/activate`
```

3. Open a terminal and pull the OOTB repository (this repository) from Github

```
git clone https://github.com/ComNets-Bremen/ops-on-the-bench.git
```

4. Install all the following packages using `pip` package manager of `Python`. You may have to update `pip` before you use.

```
pip3 install django
pip3 install rq
pip3 install django-formtools
pip3 install matplotlib
pip3 install fpdf
pip3 install dropbox
pip3 install slugify
pip3 install six
```

5. 




### Setup OOTB Worker Components


1. Open a terminal and pull the OOTB repository (this repository) from Github

```
git clone https://github.com/ComNets-Bremen/ops-on-the-bench.git
```





## Bringing Up





## Running Simulation


