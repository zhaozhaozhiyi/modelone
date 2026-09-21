#!/bin/sh
: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"
set -eu
modelone_notebook_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$modelone_notebook_root"
hubhost=${MODELONE_IMAGE_PREFIX}modelone

# 构建bigdata镜像
docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" -t  $hubhost/notebook:jupyter-ubuntu-bigdata -f bigdata/Dockerfile .
#docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --build-arg APACHE_MIRROR=https://mirrors.aliyun.com/apache --build-arg  PIPI_MIRROR_ENABLE=true --build-arg  UBUNTU_MIRROR_ENABLE=true -t  $hubhost/notebook:jupyter-ubuntu-bigdata -f bigdata/Dockerfile .
docker push $hubhost/notebook:jupyter-ubuntu-bigdata
