FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US/Pacific

RUN apt-get -o Acquire::Check-Valid-Until=false update
RUN apt-get -y upgrade

# Are those packages used anywhere?
# RUN apt-get -y install build-essential
# RUN apt-get -y install git
RUN apt-get -y install \
    wget \
    iproute2 \
    python3 \
    python3-pip \
    python-is-python3

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir -U pip==23.0.1 wheel==0.38.4 setuptools==67.6.0

COPY DentOsTestbed/Requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/Requirements.txt

COPY DentOsTestbedLib/Requirements.txt /tmp/
RUN pip3 install --no-cache-dir -r /tmp/Requirements.txt

LABEL author="Mircea Dan Gheorghe <mircea-dan.gheorghe@keysight.com>"
LABEL version="1.0"
LABEL description="DENT base env for testing"
