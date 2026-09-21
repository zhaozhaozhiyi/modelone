#!/bin/bash
set -euo pipefail
stage=${STAGE:-}
case "$stage" in
  1|11|2|22|3|33|4|44) ;;
  *) echo 'Select an explicit supported STAGE' >&2; exit 2 ;;
esac
# 先检查下面的命令中的参数，比如内网仓库的地址，docker根目录的地址，nfs的地址，rancher server的加入地址，机器的网卡名称
# =================安装docker==================
if [ "$stage" = "1" ]; then

sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release vim git wget net-tools

sudo mkdir -p /etc/apt/keyrings
rm -rf /etc/apt/keyrings/docker.gpg
rm -rf /etc/apt/sources.list.d/docker.list

curl -fsSL http://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | apt-key add -
arch=amd64
sudo add-apt-repository  -y "deb [arch=${arch}] http://mirrors.aliyun.com/docker-ce/linux/ubuntu $(lsb_release -cs) stable"

apt install -y docker-ce=5:27.0.3-1~ubuntu.22.04~jammy

sudo mkdir -p /etc/docker

cat > /etc/docker/daemon.json <<EOF
{
    "registry-mirrors": ["https://hub.rat.dev/","https://docker.xuanyuan.me", "https://docker.m.daocloud.io","https://dockerproxy.com"],
    "dns": ["114.114.114.114","8.8.8.8"],
    "max-concurrent-downloads": 30,
    "data-root": "/data/docker",
    "insecure-registries":["docker.oa.com:8080"]
}
EOF

systemctl stop docker
systemctl daemon-reload
systemctl start docker

fi

# =================检测：安装docker==================
if [ "$stage" = "11" ]; then
  docker ps
fi
## =============挂载nfs================

if [ "$stage" = "2" ]; then
  apt update
  apt install -y nfs-kernel-server
  apt install -y nfs-common
  : "${MODELONE_NFS_SERVER:?Set the NFS server}"
  : "${MODELONE_NFS_EXPORT:?Set the NFS export path}"
  mkdir -p /data/nfs
  nfs_entry="${MODELONE_NFS_SERVER}:${MODELONE_NFS_EXPORT} /data/nfs nfs defaults 0 0"
  grep -Fxq "$nfs_entry" /etc/fstab || echo "$nfs_entry" >> /etc/fstab
  mount -a
  mkdir -p /data/nfs/k8s
  if [ ! -e /data/k8s ]; then ln -s /data/nfs/k8s /data/k8s; fi

fi
# =================检测：挂载nfs==================
if [ "$stage" = "22" ]; then
  df -h |grep nfs
fi
## =================拉取rancher镜像=====================
if [ "$stage" = "3" ]; then
  : "${MODELONE_INSTALL_ROOT:?Set MODELONE_INSTALL_ROOT to the mounted modelOne installation root}"
  sh "$MODELONE_INSTALL_ROOT/install/kubernetes/rancher/pull_rancher_images.sh"
fi
# =================检测：拉取rancher镜像==================
if [ "$stage" = "33" ]; then
  docker images |grep rancher |wc -l
fi

## ==================检测网卡对应的ip是不是对的=====================
if [ "$stage" = "4" ]; then
  ip -4 addr show dev "${MODELONE_NODE_INTERFACE:-eth0}"
fi
## ==================加入rancher集群=====================
if [ "$stage" = "44" ]; then
  : "${RANCHER_SERVER_URL:?Set the private Rancher server URL}"
  : "${RANCHER_AGENT_TOKEN:?Set the short-lived Rancher agent token}"
  : "${RANCHER_AGENT_CA_CHECKSUM:?Set the Rancher agent CA checksum}"
  RANCHER_AGENT_IMAGE="${RANCHER_AGENT_IMAGE:-rancher/rancher-agent:v2.8.5}"
  node_ip=$(ip -4 -o addr show dev "${MODELONE_NODE_INTERFACE:-eth0}" scope global | awk 'NR == 1 {split($4, address, "/"); print address[1]}')
  : "${node_ip:?No IPv4 address found on the selected interface}"
  sudo -n docker run -d --privileged --restart=unless-stopped --net=host -v /etc/kubernetes:/etc/kubernetes -v /var/run:/var/run "$RANCHER_AGENT_IMAGE" --server "$RANCHER_SERVER_URL" --token "$RANCHER_AGENT_TOKEN" --ca-checksum "$RANCHER_AGENT_CA_CHECKSUM" --worker --node-name "$node_ip"
fi
