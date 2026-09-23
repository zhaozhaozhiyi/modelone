> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。

# 1、gpu机器环境的准备  

## 机器安装驱动

参考 install/kubernetes/rancher/install_gpu.md

## docker/containerd 下 nvidia 运行时

参考 

 - install/kubernetes/rancher/init_node_gpu.md

# 2，部署k8s集群和部署modelOne

如果已经部署了k8s和modelOne，这里只是将gpu机器加入到k8s集群，这里可以忽略，

如果还没有部署k8s和modelOne，可以参考《平台单机部署》先部署k8s集群和modelOne

# 3、将机器加入k8s集群

加入k8s集群后为机器添加标签，标签只是用户管理和选择机型设备。
```
gpu=true       用于表示 gpu设备
vgpu=true       用于表示 vgpu设备
gpu-type=V100  用于表示gpu型号，或者gpu-type=T4

train=true     用于训练
service=true   用于推理
notebook=true  用于开发

org=public   用于表示属于的public资源组
```

# 4、部署k8s gpu插件（自带了）

gpu/nvidia-device-plugin.yml  
daemonset 	kube-system/nvidia-device-plugin.会在机器上部署pod，用于scheduler识别改机器可用gpu算力。

# 5、检查k8s机器 可占用gpu资源。

kubectl get node -o yaml

```
status:
  capacity:
    cpu: '20'
    memory: 81846828Ki
    nvidia.com/gpu: '1'                # 英伟达gpu的资源占用
```
如果不存在可占用gpu，那可能是因为机器上非k8s之外存在占用。需要先关停机器上的gpu占用进程，然后重启kubelet。 rancher重启kubelet的方法是 docker restart kubelet

# 6、部署k8s监控组件（自带了）

daemonset 	monitoring/dcgm-exporter.会在机器上部署pod，用于监控gpu上的使用率

# 7、调度占用gpu

直接写占用卡数目，对于异构gpu环境，也可以选择占用的卡型。比如1(T4),2(V100),0.1

# 8、关于cuda版本

机器安装英伟达驱动和对应版本cuda，比如驱动 550，cuda 12.4

在k8s modelOne 容器中使用cuda版本要低于主机的cuda版本12.4，实际pytorch等代码中需要适配的cuda为镜像中cuda版本，不需要关心主机上的cuda版本

比如：在主机的cuda 12.4，在k8s中使用cuda11.8的gpu镜像，那就需要在镜像环境中安装兼容cuda 11.8的pytorch