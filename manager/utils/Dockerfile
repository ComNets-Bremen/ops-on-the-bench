# Base Ubuntu version is 16.04
FROM ubuntu:16.04


# Install all the Ubuntu packages required
RUN apt-get update -y && apt-get install -y python3-minimal python3-pip \
      build-essential bison flex libxml2-dev zlib1g-dev python-minimal wget \
	  git autoconf automake libtool python3-matplotlib vim
RUN apt-get install ccache -y


# set caching path
ENV PATH /usr/lib/ccache:$PATH


# install Python modules
RUN pip3 install --upgrade pip && pip3 install rq && pip3 install fpdf


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
RUN make MODE=release -j $(nproc)
WORKDIR /opt/


# Install OPS
RUN git clone https://github.com/ComNets-Bremen/OPS.git
WORKDIR /opt/OPS/
RUN ./bootstrap.sh
RUN ./ops-makefile-setup.sh
RUN make
WORKDIR /opt/OPS/simulations/
RUN mkdir /opt/data
ENV PATH /opt/OPS:$PATH
ENV LD_LIBRARY_PATH /opt/omnetpp-5.6.1/lib:/opt/OPS/modules/KeetchiLib/lib/.libs:/opt/OPS/modules/inet/src:$LD_LIBRARY_PATH


# copy scripts and other files
COPY worker.py /opt/OPS/simulations/
RUN chmod +x /opt/OPS/simulations/worker.py
COPY opsrun.py /opt/OPS/simulations/
RUN chmod +x /opt/OPS/simulations/opsrun.py
RUN mkdir /opt/OPS/simulations/utils
COPY worker_utils.py /opt/OPS/simulations/utils/
RUN chmod +x /opt/OPS/simulations/utils/worker_utils.py
COPY worker_utils.py /opt/OPS/simulations/
RUN chmod +x /opt/OPS/simulations/worker_utils.py
COPY stat-list.txt /opt/OPS/simulations/


# start RQ worker 
ENTRYPOINT ["rq", "worker"]

