> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


### 在线安装(所有节点)
ubuntu
```shell
apt update
apt install nfs-kernel-server
apt install nfs-common
```
centos
```shell
yum install nfs-utils

```
### centos安装rpm包(所有节点)

```shell
wget https://docker-76009.sz.gfp.tencent-cloud.com/github/cube-studio/deploy/nfs/nfsrpm.tar.gz
tar -zxvf nfsrpm.tar.gz
cd nfs
rpm -ivh *.rpm --force --nodeps
```

### nfs server配置

```shell

# 修改配置文件，增加下面这一行数据，指定的ip地址为客户端的地址
# /data/nfs/ 代表nfs server本地存储目录
echo "/data/nfs/ *(rw,no_root_squash,async)" >> /etc/exports

# 加载配置文件
exportfs -arv
systemctl enable rpcbind.service 
systemctl enable nfs-server.service
systemctl start rpcbind.service
systemctl start nfs-server.service

#验证
[root@nfs ~]# showmount -e localhost
Export list for localhost:
/data/nfs                     *
```

### nfs client配置

```shell
#查看nfs server 信息

[root@node02 ~]# showmount -e 172.16.101.13
Export list for 172.16.101.13:
/data/nfs      *

# 系统层面添加挂载添加一行，重启自动添加
echo "172.16.101.13:/data/nfs  /data/nfs   nfs   defaults  0  0" >> /etc/fstab
mount -a 

# 或者使用命令行
mount -t nfs 172.16.101.13:/data/nfs /data/nfs

#验证
df -h /data/nfs

# 软链到CubeStudio的目录
mkdir -p /data/nfs/k8s
ln -s /data/nfs/k8s /data/

#输出 表示挂载成功
[root@node02 ~]# df -h /data/nfs
Filesystem                Size  Used Avail Use% Mounted on
172.16.101.13:/data/nfs  3.5T  626M  3.5T   1% /data/k8s

```