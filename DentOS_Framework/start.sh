#!/bin/bash

export DOCKER_BUILDKIT=1
PWD=$(pwd)
COMMAND="/bin/bash"

# Build base image
docker build -f Dockerfile.base -t dent-testing-base:latest .

# Build working image
docker build -f Dockerfile.testing -t dent-testing:latest .

if [ ! -z $1 ]; then
    COMMAND=$@
fi

# docker run -ti --rm --name dent-testing dent-testing:latest /bin/bash
docker run \
    -ti --rm \
    --mount=type=bind,target=/DENT/DentOsTestbed,source=$PWD/DentOsTestbed \
    --mount=type=bind,target=/DENT/DentOsTestbedDiscovery,source=$PWD/DentOsTestbedDiscovery \
    --mount=type=bind,target=/DENT/DentOsTestbedLib,source=$PWD/DentOsTestbedLib \
    --name dent-testing \
    dent-testing:latest \
    $COMMAND
