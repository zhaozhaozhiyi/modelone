#!/bin/sh
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"
set -eu
modelone_notebook_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$modelone_notebook_root"
hubhost=${MODELONE_IMAGE_PREFIX}modelone

# Stage owned examples from this checkout before the Docker build.
modelone_repo_root="$(git rev-parse --show-toplevel)"
mkdir -p deeplearning/modelone-examples
cp -R "$modelone_repo_root/aihub/deep-learning/." deeplearning/modelone-examples/

# 构建deeplearning镜像
docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" -t  $hubhost/notebook:jupyter-ubuntu-deeplearning -f deeplearning/Dockerfile .
docker push $hubhost/notebook:jupyter-ubuntu-deeplearning
