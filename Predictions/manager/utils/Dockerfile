# Base Ubuntu version is 18.04
FROM ubuntu:18.04

ENV TZ="Europe/Berlin"
ARG DEBIAN_FRONTEND="noninteractive"

# Install all the Ubuntu packages required
RUN apt-get update -y
RUN apt-get install -y apt-utils

# rm python asasp (required for INET 4)
RUN apt-get install -y python-minimal

RUN apt-get install -y python3-minimal python3-pip \
      build-essential bison flex libxml2-dev zlib1g-dev wget \
      git autoconf automake libtool python3-matplotlib vim
RUN apt-get install ccache -y
RUN apt-get install zip unzip -y
RUN apt-get install pv -y
RUN apt-get install curl -y


# set caching path
ENV PATH /usr/lib/ccache:$PATH


# install Python modules
RUN pip3 install fpdf
RUN pip3 install dropbox
RUN pip3 install python-slugify
RUN pip3 install rq


# These are necessary to make Click in rq happy.
# See: http://click.pocoo.org/5/python3/#python-3-surrogate-handling
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8


# get and setup OMNeT++
WORKDIR /opt/
RUN wget https://github.com/omnetpp/omnetpp/releases/download/omnetpp-5.6.1/omnetpp-5.6.1-src-core.tgz -O omnetpp-5.6.1-src-core.tgz --progress=dot:giga
RUN tar xf omnetpp-5.6.1-src-core.tgz && rm omnetpp-5.6.1-src-core.tgz
ENV PATH /opt/omnetpp-5.6.1/bin:$PATH
WORKDIR omnetpp-5.6.1
RUN ./configure WITH_TKENV=no WITH_QTENV=no WITH_OSG=no WITH_OSGEARTH=no
RUN make MODE=release -j$(nproc)
WORKDIR /opt/


# Install OPS
RUN git clone https://github.com/ComNets-Bremen/OPS.git
WORKDIR /opt/OPS/
RUN ./bootstrap.sh
RUN ./ops-makefile-setup.sh
RUN make MODE=release -j$(nproc)
RUN mkdir /opt/data
ENV PATH /opt/OPS:$PATH
ENV LD_LIBRARY_PATH /opt/omnetpp-5.6.1/lib:/opt/OPS/modules/KeetchiLib/lib/.libs:/opt/OPS/modules/inet/src:$LD_LIBRARY_PATH

## Install default simulation traces
# WORKDIR /opt/
# RUN wget https://seafile.zfn.uni-bremen.de/f/291602b767e642d49827/?dl=1 -O ootb-traces.tar.gz --progress=dot:giga
# RUN tar xf ootb-traces.tar.gz  && rm ootb-traces.tar.gz

# copy scripts and other files
COPY init-n-begin.sh /opt/OPS/simulations/
RUN chmod +x /opt/OPS/simulations/*.sh
COPY worker.py /opt/OPS/simulations/
COPY opsrun.py /opt/OPS/simulations/
COPY worker_utils.py /opt/OPS/simulations/
COPY dropboxops.py /opt/OPS/simulations/
COPY seafileops.py /opt/OPS/simulations/
COPY localstoreops.py /opt/OPS/simulations/
COPY stat-list.txt /opt/OPS/simulations/
COPY net-list.txt /opt/OPS/simulations/
RUN chmod +x /opt/OPS/simulations/*.py
RUN mkdir /opt/OPS/simulations/utils
COPY worker.py /opt/OPS/simulations/utils/
COPY opsrun.py /opt/OPS/simulations/utils/
COPY worker_utils.py /opt/OPS/simulations/utils/
COPY dropboxops.py /opt/OPS/simulations/utils/
COPY localstoreops.py /opt/OPS/simulations/utils/
COPY seafileops.py /opt/OPS/simulations/utils/
COPY stat-list.txt /opt/OPS/simulations/utils/
COPY net-list.txt /opt/OPS/simulations/utils/
RUN chmod +x /opt/OPS/simulations/utils/*.py

# set current folder
WORKDIR /opt/OPS/simulations/

# perform initial work and start RQ (REDIS) worker 
ENTRYPOINT ["/bin/bash", "-c", "/opt/OPS/simulations/init-n-begin.sh"]

