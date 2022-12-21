#!/bin/bash

export DOCKER_BUILDKIT=1
PWD=$(pwd)

# Build base image
docker build -f Dockerfile.base -t dent-testing-base:latest .

# Build working image
docker build -f Dockerfile.dut -t dent-dut:latest .

# Run
docker run \
    -ti --rm \
    --cap-add=NET_ADMIN \
    --name dent-dut \
    dent-dut:latest \
    /bin/bash
