#!/bin/bash
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"

set -ex

docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --network=host -t ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901 -f Dockerfile  .
docker push ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901




#docker manifest rm ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901
#docker manifest create ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901 ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901-amd64 ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250918-npu
#docker manifest push ${MODELONE_IMAGE_PREFIX}modelone/yolov8:20250901

