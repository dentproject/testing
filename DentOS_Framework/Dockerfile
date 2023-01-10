FROM ubuntu:jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=US/Pacific

RUN apt -y update
RUN apt -y upgrade

RUN apt -y install build-essential
RUN apt -y install git
RUN apt -y install wget

RUN apt -y install python3
RUN apt -y install python3-setuptools
RUN apt -y install python3-pip
RUN apt -y install python-is-python3

COPY . /dent-fw
WORKDIR /dent-fw

RUN pip3 install -r ./DentOsTestbed/Requirements.txt
RUN pip3 install ./DentOsTestbed

RUN pip3 install ./DentOsTestbedDiscovery

RUN pip3 install -r ./DentOsTestbedLib/Requirements.txt
RUN pip3 install ./DentOsTestbedLib

LABEL author="Mircea Dan Gheorghe <mircea-dan.gheorghe@keysight.com>"
LABEL version="1.0"
LABEL description="DENT env for testing"
