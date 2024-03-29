#!/bin/bash

export DOCKER_BUILDKIT=1

PWD=$(pwd)
COMMAND="/bin/bash"
SCRIPT_DIR=$(dirname "$0")
DOCKERFILE_DIR=$SCRIPT_DIR

# Build base image
docker build -f "$DOCKERFILE_DIR"/Dockerfile.base -t dent/test-framework-base:latest .

# Build working image
docker build -f "$DOCKERFILE_DIR"/Dockerfile.auto -t dent/test-framework-dev:latest .

if [ -n "$1" ]; then
    COMMAND="$*"
fi

docker run \
    -ti --rm \
    --mount=type=bind,target=/DENT/DentOsTestbed,source="$PWD"/DentOsTestbed \
    --mount=type=bind,target=/DENT/DentOsTestbedDiscovery,source="$PWD"/DentOsTestbedDiscovery \
    --mount=type=bind,target=/DENT/DentOsTestbedLib,source="$PWD"/DentOsTestbedLib \
    --name dent-testing-"$USER" \
    dent/test-framework-dev:latest \
    "$COMMAND"
