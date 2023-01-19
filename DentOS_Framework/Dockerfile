FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US/Pacific

RUN apt-get -y update
RUN apt-get -y upgrade

RUN apt-get -y install build-essential
RUN apt-get -y install git
RUN apt-get -y install wget

RUN apt-get -y install python3
RUN apt-get -y install python3-setuptools
RUN apt-get -y install python3-pip
RUN apt-get -y install python-is-python3

COPY . /dent-fw
WORKDIR /dent-fw

RUN pip3 install --no-cache-dir -r ./DentOsTestbed/Requirements.txt
RUN pip3 install --no-cache-dir ./DentOsTestbed

RUN pip3 install --no-cache-dir ./DentOsTestbedDiscovery

RUN pip3 install --no-cache-dir -r ./DentOsTestbedLib/Requirements.txt
RUN pip3 install --no-cache-dir ./DentOsTestbedLib

RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

LABEL author="Mircea Dan Gheorghe <mircea-dan.gheorghe@keysight.com>"
LABEL version="1.0"
LABEL description="DENT env for testing"
