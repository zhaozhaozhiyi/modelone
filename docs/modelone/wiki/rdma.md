> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。

# 概述  
  
RDMA（Remote Direct Memory Access）是新一代的网络通信技术，它允许计算机之间直接进行内存对内存的数据传输，而不需要经过操作系统或中央处理器的处理。在大规模的分布式训练中，通过使用RDMA有效解决网络传输中服务器端数据处理的延迟问题，从而实现高吞吐、低延迟的网络通信，提升训练效率。  
  
本文档用于介绍在云原生AI的环境下使用 RDMA 网络进行分布式训练。  
  
说明：  
1、由于 RDMA 网络的特殊性，以下示例在自建k8s集群中可能无法适用。  
2、IB和RoCE在使用上几乎无区别，如无特别说明以下均以RoCE为例，IB在应用侧无需更改。  
3、业务镜像中需要使用 nccl 依赖库，这里推荐使用 NVIDIA GPU Cloud（NGC）提供的基础镜像。NGC 提供的基础镜像通常会包含 nccl 依赖库，并且已经预先配置和优化了许多常用的深度学习框架和工具。使用 NGC 基础镜像可以简化您的设置和配置过程，并确保您能够顺利使用 nccl 进行 GPU 加速计算和深度学习任务。  
  
# 使用前提  
  
已经创建集群，且集群中至少有2台具有RDMA网络的GPU实例。  
GPU实例镜像中包含ofed和nvidia驱动，这里推荐使用百度智能云提供的GPU镜像，已包含OFED驱动，无需手动安装。  
集群已安装 云原生AI CCE RDMA Device Plugin、 CCE GPU Manager 、 CCE AI Job Scheduler 和 CCE Deep Learning Frameworks Operator 组件。  

# 环境验证  

登录集群内具有 RDMA 网络的GPU节点，运行以下命令验证主机环境。  
  
# 验证 ofed 驱动  

```
$ ofed_info -s         #roce驱动版本  
MLNX_OFED_LINUX-5.8-1.1.2.1:  
```

# 验证 Nvidia GPU 驱动  

```bash
nvidia-smi  #nvidia gpu驱动  
+-----------------------------------------------------------------------------+  
| NVIDIA-SMI 470.141.03   Driver Version: 470.141.03   CUDA Version: 11.4     |  
|-------------------------------+----------------------+----------------------+  
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |  
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |  
|                               |                      |               MIG M. |  
|===============================+======================+======================|  
|   0  NVIDIA A100-SXM...  On   | 00000000:53:00.0 Off |                    0 |  
| N/A   29C    P0    64W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   1  NVIDIA A100-SXM...  On   | 00000000:59:00.0 Off |                    0 |  
| N/A   32C    P0    61W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   2  NVIDIA A100-SXM...  On   | 00000000:6E:00.0 Off |                    0 |  
| N/A   33C    P0    67W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   3  NVIDIA A100-SXM...  On   | 00000000:73:00.0 Off |                    0 |  
| N/A   29C    P0    60W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   4  NVIDIA A100-SXM...  On   | 00000000:8D:00.0 Off |                    0 |  
| N/A   29C    P0    60W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   5  NVIDIA A100-SXM...  On   | 00000000:92:00.0 Off |                    0 |  
| N/A   32C    P0    65W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   6  NVIDIA A100-SXM...  On   | 00000000:C9:00.0 Off |                    0 |  
| N/A   33C    P0    64W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  
|   7  NVIDIA A100-SXM...  On   | 00000000:CF:00.0 Off |                    0 |  
| N/A   28C    P0    62W / 400W |      0MiB / 81251MiB |      0%      Default |  
|                               |                      |             Disabled |  
+-------------------------------+----------------------+----------------------+  


+-----------------------------------------------------------------------------+  
| Processes:                                                                  |  
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |  
|        ID   ID                                                   Usage      |  
|=============================================================================|  
|  No running processes found                                                 |  
+-----------------------------------------------------------------------------+  
```
# 查询 RDMA 网卡  
```bash
show_gids  
DEV	PORT	INDEX	GID					IPv4  		VER	DEV  
---	----	-----	---					------------  	---	---  
mlx5_0	1	0	fe80:0000:0000:0000:f820:20ff:fe28:c769			v1	eth0  
mlx5_0	1	1	fe80:0000:0000:0000:f820:20ff:fe28:c769			v2	eth0  
mlx5_0	1	2	0000:0000:0000:0000:0000:ffff:0a00:3c03	10.0.60.3  	v1	eth0  
mlx5_0	1	3	0000:0000:0000:0000:0000:ffff:0a00:3c03	10.0.60.3  	v2	eth0  
mlx5_1	1	0	fe80:0000:0000:0000:eaeb:d3ff:fecc:c920			v1	eth1  
mlx5_1	1	1	fe80:0000:0000:0000:eaeb:d3ff:fecc:c920			v2	eth1  
mlx5_1	1	2	0000:0000:0000:0000:0000:ffff:190b:8002	25.11.128.2  	v1	eth1  
mlx5_1	1	3	0000:0000:0000:0000:0000:ffff:190b:8002	25.11.128.2  	v2	eth1  
mlx5_2	1	0	fe80:0000:0000:0000:eaeb:d3ff:fecc:c921			v1	eth2  
mlx5_2	1	1	fe80:0000:0000:0000:eaeb:d3ff:fecc:c921			v2	eth2  
mlx5_2	1	2	0000:0000:0000:0000:0000:ffff:190b:8022	25.11.128.34  	v1	eth2  
mlx5_2	1	3	0000:0000:0000:0000:0000:ffff:190b:8022	25.11.128.34  	v2	eth2  
mlx5_3	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe6c:51d2			v1	eth3  
mlx5_3	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe6c:51d2			v2	eth3  
mlx5_3	1	2	0000:0000:0000:0000:0000:ffff:190b:8042	25.11.128.66  	v1	eth3  
mlx5_3	1	3	0000:0000:0000:0000:0000:ffff:190b:8042	25.11.128.66  	v2	eth3  
mlx5_4	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe6c:51d3			v1	eth4  
mlx5_4	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe6c:51d3			v2	eth4  
mlx5_4	1	2	0000:0000:0000:0000:0000:ffff:190b:8062	25.11.128.98  	v1	eth4  
mlx5_4	1	3	0000:0000:0000:0000:0000:ffff:190b:8062	25.11.128.98  	v2	eth4  
mlx5_5	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe33:1366			v1	eth5  
mlx5_5	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe33:1366			v2	eth5  
mlx5_5	1	2	0000:0000:0000:0000:0000:ffff:190b:8082	25.11.128.130  	v1	eth5  
mlx5_5	1	3	0000:0000:0000:0000:0000:ffff:190b:8082	25.11.128.130  	v2	eth5  
mlx5_6	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe33:1367			v1	eth6  
mlx5_6	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe33:1367			v2	eth6  
mlx5_6	1	2	0000:0000:0000:0000:0000:ffff:190b:80a2	25.11.128.162  	v1	eth6  
mlx5_6	1	3	0000:0000:0000:0000:0000:ffff:190b:80a2	25.11.128.162  	v2	eth6  
mlx5_7	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe6c:68ae			v1	eth7  
mlx5_7	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe6c:68ae			v2	eth7  
mlx5_7	1	2	0000:0000:0000:0000:0000:ffff:190b:80c2	25.11.128.194  	v1	eth7  
mlx5_7	1	3	0000:0000:0000:0000:0000:ffff:190b:80c2	25.11.128.194  	v2	eth7  
mlx5_8	1	0	fe80:0000:0000:0000:eaeb:d3ff:fe6c:68af			v1	eth8  
mlx5_8	1	1	fe80:0000:0000:0000:eaeb:d3ff:fe6c:68af			v2	eth8  
mlx5_8	1	2	0000:0000:0000:0000:0000:ffff:190b:80e2	25.11.128.226  	v1	eth8  
mlx5_8	1	3	0000:0000:0000:0000:0000:ffff:190b:80e2	25.11.128.226  	v2	eth8  
```

# 提交任务  

NCCL是NVIDIA的集合通信库，能实现Collective通信和点对点通信，NCCL内部已经实现了RDMA通信，同时NCCL可以根据环境中网卡类型和拓扑关系，自行选择一个最优的通信路径，目前主流的分布式训练框架都已支持NCCL。  
  
下面介绍将介绍如何在云原生AI 上通过 YAML或者控制台的方式，提交基于NCCL的RDMA分布式训练任务。  
  
# YAML方式提交任务  
## 准备  
已通过kubectl连接kubernetes集群。具体操作，请参见通过Kubectl连接集群。  
  
## 任务示例  
以下是一个swin-transformer基于NCCL的Pytorch分布式训练任务的示例：  
```bash
apiVersion: "kubeflow.org/v1"  
kind: "PyTorchJob"  
metadata:  
  name: "pytorch-swin-transformer-nccl"  
spec:  
  pytorchReplicaSpecs:  
    Master:  
      replicas: 1  
      restartPolicy: OnFailure  
      template:  
        metadata:  
          annotations:  
            sidecar.istio.io/inject: "false"  
        spec:  
          containers:  
            - name: pytorch  
              image: registry.baidubce.com/cce-ai-native/swin-transformer-torch:v2.0  
              imagePullPolicy: IfNotPresent  
              command:  
              - /bin/sh  
              - -c  
              - python -m torch.distributed.launch --nproc_per_node 8 --nnodes $WORLD_SIZE --node_rank $RANK --master_addr $HOSTNAME --master_port $MASTER_PORT main.py --cfg configs/swin/swin_large_patch4_window7_224_22k.yaml --pretrained swin_large_patch4_window7_224_22k.pth --data-path /imagenet --batch-size 128 --accumulation-steps 2  
              env:  
                - name: NCCL_DEBUG  
                  value: "INFO"  
                - name: NCCL_IB_DISABLE  
                  value: "0"  
              securityContext:  
                capabilities:  
                  add: [ "IPC_LOCK" ]  
              resources:  
                limits:  
                  nvidia.com/gpu: 8  
                  rdma/hca: 1  
              volumeMounts:  
                - mountPath: /imagenet  
                  name: dataset  
                - mountPath: /dev/shm  
                  name: cache-volume  
          schedulerName: volcano  
          volumes:  
            - name: dataset  
              persistentVolumeClaim:  
                claimName: imagenet-22k-pvc  
            - emptyDir:  
                medium: Memory  
              name: cache-volume  
    Worker:  
      replicas: 1  
      restartPolicy: OnFailure  
      template:  
        metadata:  
          annotations:  
            sidecar.istio.io/inject: "false"  
        spec:  
          containers:  
            - name: pytorch  
              image: registry.baidubce.com/cce-ai-native/swin-transformer-torch:v2.0  
              imagePullPolicy: IfNotPresent  
              command:  
              - /bin/sh  
              - -c  
              - python -m torch.distributed.launch --nproc_per_node 8 --nnodes $WORLD_SIZE --node_rank $RANK --master_addr $MASTER_ADDR --master_port $MASTER_PORT main.py --cfg configs/swin/swin_large_patch4_window7_224_22k.yaml --pretrained swin_large_patch4_window7_224_22k.pth --data-path /imagenet --batch-size 128 --accumulation-steps 2  
              env:    
                - name: NCCL_DEBUG  
                  value: "INFO"  
                - name: NCCL_IB_DISABLE  
                  value: "0"  
              securityContext:  
                capabilities:  
                  add: [ "IPC_LOCK" ]  
              resources:  
                limits:  
                  nvidia.com/gpu: 8  
                  rdma/hca: 1  
              volumeMounts:  
                - mountPath: /imagenet  
                  name: dataset  
                - mountPath: /dev/shm  
                  name: cache-volume  
          volumes:  
            - name: dataset  
              persistentVolumeClaim:  
                claimName: imagenet-22k-pvc  
            - emptyDir:  
                medium: Memory  
              name: cache-volume  
          schedulerName: volcano  
---  
apiVersion: v1  
kind: PersistentVolume  
metadata:  
  name: imagenet-22k-pv  
spec:  
  accessModes:  
  - ReadWriteMany  
  storageClassName:  
  capacity:  
    storage: 100Gi  
  csi:  
    driver: csi-clusterfileplugin  
    volumeHandle: data-id  
    volumeAttributes:  
      parentDir: /           #必填，自定义路径  
      path: ""               #必填，pfs 挂载路径，这里需要填写相对于 parentDir 的路径  
      clusterIP: ""          #必填，pfs实例的endpoint  
      clusterPort: "8888"    #必填，当前端口固定为8888  
      clientID: ""           #非必填，pfs实例的id  
  
---  
kind: PersistentVolumeClaim  
apiVersion: v1  
metadata:  
  name: imagenet-22k-pvc  
  namespace: default  
spec:  
  accessModes:  
    - ReadWriteMany  
  storageClassName:   
  resources:  
    requests:  
      storage: 100Gi  
```

# 关键参数说明  
NCCL需要输入环境变量来使能RDMA特性，具体包括以下环境变量：  
  
备注：带 * 号的环境变量，云原生AI会基于百度智能云内部大规模分布式训练经验，在任务运行时会自动注入推荐的值，无需手动填写  


|键 |	值 |	含义	 | 备注 |
|:-- |:-- |:-- |:-- |  
|NCCL_IB_DISABLE|	0,1|	0代表NCCL使用的IB/RoCE传输；  1代表禁止NCCL使用的IB/RoCE传输。此时NCCL将退回到使用IP套接字	| -- |  
| NCCL_IB_HCA* |	mlx5_1 ~ mlx5_8	| NCCL_IB_HCA 变量指定使用哪些RDMA接口进行通信。  根据套餐类型填对应的值，例如：8卡的roce套餐填mlx5_1~mlx5_8，4卡为mlx5_1~mlx5_4，以此类推。  注：mlx5_0通常为tcp网络的主网卡| |
|NCCL_SOCKET_IFNAME*|	eth0|	NCCL_SOCKET_IFNAME变量指定使用哪个IP接口进行通信;  注：容器内默认是eth0| |  
|NCCL_IB_GID_INDEX*	| 动态值 |	NCCL_IB_GID_INDEX变量定义了RoCE模式中使用的全局ID索引。设置方法请参见ib show_gids命令。  注：如果是通过容器网络使用RoCE网卡，CCE的CNI插件会为容器创建对应数量的子网卡，roce网卡的GID INDEX会动态生成。如果容器内有show_gids命令，可以看到对应的值。  |
| NCCL_IB_TIMEOUT*	| 22 |	网络断点重连超时时间。   | |
| NCCL_IB_QPS_PER_CONNECTION*	 | 8	| 每个IB qp连接的连接数。  | 
| NCCL_DEBUG	| INFO	| NCCL_DEBUG变量控制从NCCL显示的调试信息。此变量通常用于调试。	|
	

云原生AI在任务运行时，会自动检测容器的roce环境，并为容器PID为1的进程自动注入NCCL_IB_HCA 、NCCL_SOCKET_IFNAME 、NCCL_IB_GID_INDEX、NCCL_IB_TIMEOUT 和 NCCL_IB_QPS_PER_CONNECTION 环境变量；通过PID1创建的子进程会继承这个环境变量，但是如果是通过sh启动的进程则无法继承。  
如果用户在yaml中声明了这几个环境变量，容器运行时则不再自动注入  

为了在rank之间共享数据，NCCL需要为IPC和固定(页面锁定)系统内存资源共享系统内存，需要在YAML中配置如下参数  
```bash
              securityContext:  
                capabilities:  
                  add: [ "IPC_LOCK" ]  #使能进程间通信  
              resources:  
                limits:  
                  baidu.com/a100_80g_cgpu: 8  
                  rdma/hca: 1  #使能RDMA资源  
              volumeMounts:  
                - mountPath: /imagenet  
                  name: dataset  
                - mountPath: /dev/shm  #使用Emptydir，为IPC提供足够的共享内存    
                  name: cache-volume  
          volumes:  
            - name: dataset  
              persistentVolumeClaim:  
                claimName: imagenet-22k-pvc  
            - emptyDir:  #使用Emptydir，为IPC提供足够的共享内存              
                medium: Memory  
              name: cache-volume  
```

此示例运行依赖开源数据集ImageNet-22K。这里使用百度云并行文件存储PFS作为共享存储，需要将上述开源数据集提前拷贝PFS挂载目录中，如何在CCE容器集群中使用并行文件存储PFS详见：这里。  

