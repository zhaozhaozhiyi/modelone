> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。

# master节点
```bash
# 关闭防火墙
systemctl stop firewalld && systemctl disable firewalld && iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
# 下载部署脚本
git clone -b v1.24.7+k3s1 https://github.com/k3s-io/k3s.git
cd k3s
# 设置版本
export INSTALL_K3S_VERSION=v1.24.7+k3s1
# 设置k8s部署配置
#export INSTALL_K3S_EXEC="--system-default-registry registry.cn-hangzhou.aliyuncs.com --write-kubeconfig ~/.kube/config --disable=traefik --cluster-cidr  10.72.0.0/16 --service-cidr  10.73.0.0/16"
export INSTALL_K3S_EXEC="--system-default-registry registry.cn-hangzhou.aliyuncs.com --write-kubeconfig ~/.kube/config --disable=traefik"
# 设置使用国内源
export INSTALL_K3S_MIRROR=cn
# 设置强制下载
export INSTALL_K3S_SYMLINK=force
#export INSTALL_K3S_FORCE_RESTART=true
# 设置镜像url
export INSTALL_K3S_MIRROR_URL=${INSTALL_K3S_MIRROR_URL:-'rancher-mirror.rancher.cn'}
# 替换github和storage 国内可以链接到的网络
export GITHUB_URL=https://githubfast.com/k3s-io/k3s/releases
export STORAGE_URL=https://k3s-ci-builds.s3.amazonaws.com
sed -i 's|^GITHUB_URL=.*|GITHUB_URL=https://githubfast.com/k3s-io/k3s/releases|' install.sh
sed -i 's|^STORAGE_URL=.*|STORAGE_URL=https://k3s-ci-builds.s3.amazonaws.com|' install.sh
# 部署
sh install.sh
# 打印master的token
cat /var/lib/rancher/k3s/server/node-token

# 设置 containerd 的 mirror
cat > /etc/rancher/k3s/registries.yaml <<EOF
mirrors:
  docker.io:
    endpoint:
      - "http://hub-mirror.c.163.com"
      - "https://docker.mirrors.ustc.edu.cn"
      - "https://registry.docker-cn.com"
EOF

```

# worker节点
```bash
systemctl stop firewalld && systemctl disable firewalld && iptables -F && iptables -t nat -F && iptables -t mangle -F && iptables -X
git clone -b v1.24.7+k3s1 https://github.com/k3s-io/k3s.git
cd k3s
export INSTALL_K3S_VERSION=v1.24.7
export K3S_URL=https://myserver:6443
export K3S_TOKEN=XXX
sh install.sh
```

# 清理
```bash
/usr/local/bin/k3s-killall.sh
/usr/local/bin/k3s-uninstall.sh
```

# 重启
```bash
sudo systemctl stop k3s
sudo systemctl start k3s
sudo systemctl stop k3s-agent
sudo systemctl start k3s-agent
```

# 部署modelOne

部署完k3s，就可以按照单机部署modelOne来部署modelOne了

将k8s集群的kubeconfig文件复制到install/kubernetes/config文件中，然后执行如下命令，其中xx.xx.xx.xx为机器内网的ip（不是外网ip）
```
# 在k8s worker机器上执行
sh start.sh xx.xx.xx.xx
```
