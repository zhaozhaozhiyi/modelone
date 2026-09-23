> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 初始化机器环境(每台机器)

参考 install/kubernetes/rancher/install_docker.md安装docker

或者

参考 install/kubernetes/rancher/install_containerd.md安装containerd

##### 修改主机名

主机名不要有大写，保持小写主机名
```
hostnamectl set-hostname [新主机名]
```
修改后重新进入终端，主机名才会生效

```bash
# ubuntu安装基础依赖
apt install -y socat conntrack ebtables ipset ipvsadm
# centos安装基础依赖
yum install -y socat conntrack ebtables ipset ipvsadm
# 关闭firewalld服务
systemctl stop firewalld
systemctl disable firewalld
# 禁用iptable
systemctl stop iptables
systemctl disable iptables
# 禁用selinux
#setenforce 1
#echo "SELINUX=disabled" > /etc/selinux/config
#临时关闭swap分区
swapoff -a
```

# 搭建 k8s+kubesphere (主节点)

> 注意：机器最低规格为：8C16G ；kubectl 版本要1.24 ；之前安装过 KS 要提前清理下环境。

* 下载 KubeKey 

如果下载不成功，可以多执行几次

```shell
export KKZONE=cn
curl -sfL https://get-kk.kubesphere.io | VERSION=v3.1.2 sh -
chmod +x kk
```

* 清理 kubeconfig，不然会导致其他 node 节点 无法使用 kubectl

```shell
rm -rf  /root/.kube/config
```

*  安装 1.25 版本的 k8s

自定义部署最好不要启用servicemesh和monitoring
```
# 使用docker作为运行时
export KKZONE=cn
./kk create cluster -y --with-kubernetes v1.25.16 --container-manager docker

# 使用containerd作为运行时
export KKZONE=cn
./kk create cluster -y --with-kubernetes v1.25.16 --container-manager containerd

如果自己使用kubeshpere可以安装，不使用的话可以不安装kubesphere
./kk create cluster -y --with-kubernetes v1.25.16 --container-manager docker --with-kubesphere v3.4.1 
```

详细安装步骤可以参考 KubeSphere [官方文档](https://kubesphere.io/zh/docs/v3.4/quick-start/all-in-one-on-linux/)

kubesphere默认账号密码：admin/P@88w0rd

# 部署modelOne(主节点)

1、服务nodeport可用端口范围要放大到10~60000

````bash
vim /etc/kubernetes/manifests/kube-apiserver.yaml

修改添加apiserver配置

spec:
  containers:
  - command:
    - kube-apiserver
    - --service-node-port-range=1-65535      # 添加这一行
    - --advertise-address=172.16.0.17

修改后，通过reboot命令重启机器

````
2、如果使用containerd运行时，替换脚本中的docker命令
```bash
# 安装containerd下的cli
export TARGETARCH=amd64
curl -L  https://github.com/containerd/nerdctl/releases/download/v1.7.2/nerdctl-1.7.2-linux-${TARGETARCH}.tar.gz | tar xzv -C /usr/local/bin nerdctl

# 替换拉取文件中的拉取命令
cd install/kubernetes/
sed -i 's/^docker/nerdctl/g' pull_images.sh

```

3、对于kubekey部署的ipvs模式的k8s，

  （1）要将install/kubernetes/start.sh脚本最后面的`kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"externalIPs":["'"$1"'"]}}'`注释掉。取消注释代码`kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"type":"NodePort"}}'`

  （2）将配置文件install/kubernetes/cube/overlays/config/config.py中的 CONTAINER_CLI的值 改为 nerdctl，K8S_NETWORK_MODE的值 改为ipvs


4、将k8s集群的kubeconfig文件（默认位置：~/.kube/config）复制到install/kubernetes/config文件中，然后执行下面的部署命令，其中xx.xx.xx.xx为机器内网的ip（不是外网ip）

```
# 在k8s worker机器上执行

如果只部署了k8s，没有部署kubesphere，执行
sh start.sh xx.xx.xx.xx

如果部署了k8s 同时部署了kubesphere，执行
sh start-with-kubesphere.sh xx.xx.xx.xx
```

# 可能的问题

参考<<平台单机部署>> 中的 “部署后排查” 环节

# 配置prometheus替换为kubesphere的

grafana中数据源地址替换为http://prometheus-k8s.kubesphere-monitoring-system.svc:9090

配置文件config.py中

PROMETHEUS 修改为 prometheus-k8s.kubesphere-monitoring-system:9090

# 卸载 KubeSphere 和 Kubernetes

```bash
./kk delete cluster
```
