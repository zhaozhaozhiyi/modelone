#!/bin/bash

set -euo pipefail

: "${MODELONE_NODE_IPS_FILE:?Set MODELONE_NODE_IPS_FILE to a private newline-delimited node list}"
: "${MODELONE_SSH_USER:?Set MODELONE_SSH_USER to the SSH user configured with keys}"

mapfile -t IP_LIST < "$MODELONE_NODE_IPS_FILE"
if ((${#IP_LIST[@]} == 0)); then
    echo "MODELONE_NODE_IPS_FILE is empty" >&2
    exit 1
fi

USERNAME="$MODELONE_SSH_USER"

for IP in "${IP_LIST[@]}"
do
    echo "正在连接 $IP..."
    # 后面持续
    scp init.sh "$USERNAME@$IP:/home/" &
    ssh "$USERNAME@$IP" "echo $IP && export STAGE=44 && bash /home/init.sh" &

    echo "在 $IP 上执行完成"
done

wait

# 最后为机器统一加标签
# kubectl label nodes --all train=true cpu=true notebook=true service=true org=public --overwrite

