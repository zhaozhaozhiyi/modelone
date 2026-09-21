#!/bin/bash
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"

set -ex

docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --network=host -t ${MODELONE_IMAGE_PREFIX}modelone/demo:20230505 -f Dockerfile .
docker push ${MODELONE_IMAGE_PREFIX}modelone/demo:20230505



