: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"
set -ex
hubhost=${MODELONE_IMAGE_PREFIX}modelone

# Stage owned examples from this checkout before the Docker build.
modelone_repo_root="$(git rev-parse --show-toplevel)"
mkdir -p modelone-examples
cp -R "$modelone_repo_root/aihub/machine-learning/." modelone-examples/

# 构建machinelearning镜像
docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" -t  $hubhost/notebook:jupyter-ubuntu-machinelearning -f Dockerfile .
docker push $hubhost/notebook:jupyter-ubuntu-machinelearning
