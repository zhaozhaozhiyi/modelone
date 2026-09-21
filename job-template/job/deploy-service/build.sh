#!/bin/bash
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"

set -ex

docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --network=host -t ${MODELONE_IMAGE_PREFIX}modelone/deploy-service:20240601 -f job/deploy-service/Dockerfile .
docker push ${MODELONE_IMAGE_PREFIX}modelone/deploy-service:20240601



