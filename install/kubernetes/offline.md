

前置条件：

内网机器需要安装了docker，docker-compose，iptables

# [部署视频](/static/assets/modelone/video/%E5%86%85%E7%BD%91%E7%A6%BB%E7%BA%BF%E9%83%A8%E7%BD%B2.mp4)

# 完全无法联网的内网机器

## 安装依赖组件和数据

能连接外网的机器上执行下面的命令，拷贝到内网机器上
````bash
mkdir offline
cd offline
export MODELONE_ASSET_BASE_URL="https://<企业对象存储或CDN域名>/modelone"
# 下载kubectl 和harbor的离线安装包
# amd64版本
wget "${MODELONE_ASSET_BASE_URL%/}/install/kubectl"
wget "${MODELONE_ASSET_BASE_URL%/}/install/harbor-offline-installer-v2.11.1.tgz"

# 下载模型
wget "${MODELONE_ASSET_BASE_URL%/}/inference/resnet50.onnx"
wget "${MODELONE_ASSET_BASE_URL%/}/inference/resnet50-torchscript.pt"
wget "${MODELONE_ASSET_BASE_URL%/}/inference/resnet50.mar"
wget "${MODELONE_ASSET_BASE_URL%/}/inference/tf-mnist.tar.gz"
wget "${MODELONE_ASSET_BASE_URL%/}/inference/decisionTree_model.pkl"

# 训练,标注数据集
wget "${MODELONE_ASSET_BASE_URL%/}/pipeline/coco.zip"
wget "${MODELONE_ASSET_BASE_URL%/}/pipeline/coco2014.zip"

````

offline目录拷贝到内网机器上

连不上网的机器上

1、安装kubectl
```bash
cd offline
chmod +x kubectl  && cp kubectl /usr/bin/ && cp kubectl /usr/local/bin/
```

2、[安装内网镜像仓库](harbor/readme.md)

参考install/kubernetes/harbor/readme.md

并创建 modelone 和 rancher 项目，分别存放 Rancher 基础镜像和 modelOne 基础镜像

配置每台机器docker添加这个 insecure-registries内网的私有镜像仓，如果是https可以忽略

参考： install/kubernetes/rancher/install_docker.md

3、将其他前面下载的数据转移到个人目录下

```bash
cp -r offline /data/k8s/kubeflow/pipeline/workspace/admin/
```

## 镜像转移至内网

## 转移rancher镜像

设置 `MODELONE_IMAGE_REGISTRY` 为企业仓库 host/path，先在联网机器登录仓库，再生成独立目录：

```sh
python3 install/kubernetes/rancher/all_image.py --output dist/modelone/rancher-images
bash dist/modelone/rancher-images/push_rancher_harbor.sh
bash dist/modelone/rancher-images/rancher_image_save.sh
```

`push_rancher_harbor.sh` 才会复制并推送镜像；`pull_rancher_images.sh` 只拉取来源镜像。将整个输出目录（包括脚本、images.json、archives 和许可证）复制到离线节点，再执行 `rancher_image_load.sh`。若内网仓库可访问，可执行 `pull_rancher_harbor.sh`，无须传输压缩包。节点批量工具的阶段 3 使用 `MODELONE_RANCHER_BUNDLE_DIR` 指向这个完整离线包，只做校验和导入。

## 内网部署 k8s

使用rancher相同方法可在内网部署k8s

## 转移 modelOne 基础镜像

先重建需要品牌、安全或业务代码改造的企业镜像。脚本不会尝试从公共仓库拉取 `modelone/` 镜像，产品镜像必须已存在于企业仓库中。

```sh
python3 install/kubernetes/all_image.py --output dist/modelone/platform-images
bash dist/modelone/platform-images/push_harbor.sh
bash dist/modelone/platform-images/image_save.sh
```

默认包含受管理资源快照与基础服务清单；按实际部署补全第三方镜像。可重复传入 `--manifest <已渲染的部署文件>` 收集其中的容器、初始化容器和服务镜像，用 `--image-list <逐行镜像文件>` 补充注入器、运行时选择及自定义任务的镜像。未展开的模板表达式会报错。每次生成使用新的输出目录，避免覆盖已完成的校验记录。

镜像目标、原运行引用与来源记录在 `images.json`。第三方目标保留完整仓库层级，避免同名冲突。所有操作逐项检查结果，任一失败立即退出。`image_save.sh` 只导出本机已有目标镜像，不联网；成功后记录 SHA-256、镜像 ID 和架构。将整个目录复制到离线节点，运行 `image_load.sh`。它先验证全部压缩包，再开始导入；导入后再次核对镜像 ID。Docker 打包针对本机架构，多架构仓库迁移另用资源工具的 skopeo 流程。

内网仓库已就绪时也可使用 `pull_harbor.sh`。部署文件和运行配置中的镜像必须改成计划中的 `target`，工具不再恢复旧公共镜像别名，避免运行时继续从外部拉取。对 Argo 清单和其他独立基础设施清单，使用同一份计划批量重写并只把输出目录交付：

```sh
python3 scripts/rewrite_deployment_images.py \
  --plan dist/modelone/platform-images/images.json \
  --output-dir dist/modelone/platform-manifests/argo \
  --manifest install/kubernetes/argo/install-3.4.3-all.yaml \
  --manifest install/kubernetes/argo/workflow.yaml
```

该命令会重写每个 `image`、`initContainers[].image` 以及控制器 `args`/`command` 中的计划镜像引用；缺少镜像、模板表达式或重复输出文件名会直接失败。集群安装使用 `dist/modelone/platform-manifests` 中的重写文件，不直接应用源码清单。镜像包仅是离线安装的一部分；软件包、控制器注入镜像、模型数据、许可证清单与离线网络检查仍须完整验收。

## 内网部署 modelOne

1、在每个节点执行生成的 `image_load.sh` 校验并导入完整离线包，或通过 `pull_harbor.sh` 从企业内网仓库拉取。平台部署前审核节点初始化配置，避免直接套用发行版和网络配置示例。

2、在联网环境完成企业镜像计划、Argo 清单重写和发布清单扫描，确保 `dist/modelone/kubernetes.yaml` 与 `dist/modelone/platform-manifests/argo/install-3.4.3-all.yaml` 已随交付包提供。集群启动脚本拒绝直接应用源码清单。

3、复制 k8s 的 config 文件，设置 `MODELONE_RELEASE_DIR`（默认 `../../dist/modelone`）和可选的 `MODELONE_SERVICE_EXTERNAL_IP`，再执行 `bash install/kubernetes/start.sh <节点地址>`。脚本会把节点地址注入 modelOne 工作负载，不会修改源码配置文件。

## web界面的部分内网修正

1、web界面hubsecret改为内部仓库的账号密码

2、修改配置文件中的内网仓库信息和内外网ip

3、自带的目标识别pipeline中，第一个数据拉取任务启动命令改为，`cp offline/coco.zip ./ && ...`

4、自带的推理服务启动命令 由`wget https://xxxx/xx/.zip` 部分改为 `cp /mnt/admin/offline/xx.zip ./`

# 内网中有可以联网的机器

##  联网机器设置代理服务器

联网机器上设置nginx代理软件源，参考install/kubernetes/nginx-https/apt-yum-pip-source.conf

启动nginx代理访问

需要监听80和443端口
```bash
docker run --name proxy-repo -d --restart=always --network=host -v $PWD/nginx-https/apt-yum-pip-source.conf:/etc/nginx/nginx.conf nginx 
```

## 在内网机器上配置host

host
```bash
<出口服务器的IP地址>    mirrors.aliyun.com
<出口服务器的IP地址>    <企业镜像仓库域名>
<出口服务器的IP地址>    registry-1.docker.io
<出口服务器的IP地址>    auth.docker.io
<出口服务器的IP地址>    hub.docker.com
<出口服务器的IP地址>    www.modelscope.cn
<出口服务器的IP地址>    modelscope.oss-cn-beijing.aliyuncs.com
<出口服务器的IP地址>    archive.ubuntu.com
<出口服务器的IP地址>    security.ubuntu.com
<出口服务器的IP地址>    cloud.r-project.org
<出口服务器的IP地址>    deb.nodesource.com
<出口服务器的IP地址>    <企业对象存储或CDN域名>
```

添加新的host要重启下kubelet   docker restart kubelet

如果代理机器没法占用80和443，需要使用iptable尝试转发。

iptables
```bash
sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -d mirrors.aliyun.com -j DNAT --to-destination <出口服务器的IP地址>:<出口服务器的端口>
```

## k8s配置域名解析

k8s中修改 kube-system命名空间，coredns的configmap，添加 需要访问的地址 的地址映射
```bash
{
	"Corefile": ".:53 {
		    errors
		    health {
		      lameduck 5s
		    }
		    ready
		    kubernetes cluster.local in-addr.arpa ip6.arpa {
		      pods insecure
		      fallthrough in-addr.arpa ip6.arpa
		    }
		    # 自定义host
		    hosts {
		        <出口服务器的IP地址>    mirrors.aliyun.com
                <出口服务器的IP地址>    <企业镜像仓库域名>
                <出口服务器的IP地址>    registry-1.docker.io
                <出口服务器的IP地址>    auth.docker.io
                <出口服务器的IP地址>    hub.docker.com
                <出口服务器的IP地址>    www.modelscope.cn
                <出口服务器的IP地址>    modelscope.oss-cn-beijing.aliyuncs.com
                <出口服务器的IP地址>    archive.ubuntu.com
                <出口服务器的IP地址>    security.ubuntu.com
                <出口服务器的IP地址>    cloud.r-project.org
                <出口服务器的IP地址>    deb.nodesource.com
                <出口服务器的IP地址>    <企业对象存储或CDN域名>
		      fallthrough
		    }
		    prometheus :9153
		    forward . \"/etc/resolv.conf\"
		    cache 30
		    loop
		    reload
		    loadbalance
		} # STUBDOMAINS - Rancher specific change
		"
}
```
重启coredns的pod

## 容器里面使用放开的域名

pip配置https源:
```bash
pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple
```

apt配置https源: 修改/etc/apt/source.list

ubuntu 20.04
```bash

deb https://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-updates main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-backports main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-security main restricted universe multiverse

deb https://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
deb-src https://mirrors.aliyun.com/ubuntu/ focal-proposed main restricted universe multiverse
```

yum 配置https源：下载阿里的源
```bash
wget -O /etc/yum.repos.d/CentOS-Base.repo https://mirrors.aliyun.com/repo/Centos-8.repo
```
