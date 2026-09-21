# 创建初始化目录
systemctl stop firewalld
systemctl disable firewalld
systemctl stop iptables
systemctl disable iptables
systemctl stop ip6tables
systemctl disable ip6tables
systemctl stop nftables
systemctl disable nftables

ufw disable

iptables -P FORWARD ACCEPT
iptables -P INPUT ACCEPT
iptables -P OUTPUT ACCEPT

mkdir -p /data/k8s/kubeflow/pipeline/workspace /data/k8s/kubeflow/pipeline/archives /data/k8s/infra/mysql /data/k8s/kubeflow/minio/mlpipeline /data/k8s/kubeflow/global
mkdir -p /data/k8s/monitoring/grafana/ /data/k8s/monitoring/prometheus/ /data/k8s/kubeflow/labelstudio/
chmod -R 777 /data/k8s/monitoring/grafana/ /data/k8s/monitoring/prometheus/ /data/k8s/kubeflow/labelstudio/

# 关闭swap分区
swapoff -a
# 导入由 modelOne 镜像计划生成的企业离线包；不会从公共仓库拉取镜像。
script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
MODELONE_IMAGE_BUNDLE_DIR="${MODELONE_IMAGE_BUNDLE_DIR:?Set MODELONE_IMAGE_BUNDLE_DIR to a generated offline image package}" \
  sh "$script_dir/pull_images_mini.sh"

