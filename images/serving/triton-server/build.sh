: "${MODELONE_IMAGE_REGISTRY:?Set the enterprise registry host/path}"
MODELONE_IMAGE_PREFIX="${MODELONE_IMAGE_REGISTRY%/}/"
set -ex
hubhost=${MODELONE_IMAGE_PREFIX}modelone

arr=("tritonserver:24.01-py3" "tritonserver:23.12-py3" "tritonserver:22.12-py3" "tritonserver:21.12-py3" "tritonserver:20.12-py3")

for value in "${arr[@]}"
do
    echo $value
    docker build --build-arg MODELONE_IMAGE_PREFIX="$MODELONE_IMAGE_PREFIX" --network=host -t $hubhost/$value --build-arg FROM_IMAGES=nvcr.io/nvidia/$value .
    docker push $hubhost/$value
done



