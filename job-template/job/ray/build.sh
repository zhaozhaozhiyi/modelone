#!/bin/bash
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"

docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --network=host -t ${MODELONE_IMAGE_PREFIX}modelone/ray:gpu-20250301 -f job/ray/Dockerfile .
docker push ${MODELONE_IMAGE_PREFIX}modelone/ray:gpu-20250301



