# notebook重启问题

关于续期：因为对gpu的占用方式为独占方式，所以对于gpu notebook会定时清理，需要按时续期。

关于清理：可以通过删除config.py中的delete_notebook定时任务，关闭掉定时清理notebook

关于环境：重启后会自动执行/mnt/$USERNAME/init.sh脚本，所以可以将环境写入此脚本，重启后自动安装环境，否则就需要打包到镜像或者离线anaconda文件

# 构建notebook镜像

需要构建新镜像并在生产上替换，才能让用户使用新的notebook镜像。

四种 Jupyter 镜像共用 `notebook_init.py`。bigdata、machinelearning 和 deeplearning 的构建脚本会自动将构建目录定位到 `images/jupyter-notebook`；手工构建时同样使用这个目录作为上下文，例如 `docker build -f bigdata/Dockerfile .`。构建会安装显示名称为 `modelOne Python` 的 `modelone` 内核，供 SDK 示例直接选择；内部 conda 环境名称继续兼容既有配置。

## Notebook 初始化与 SSH

默认不启动 SSH，示例目录和 Spark 配置仍会初始化，之后才启动 IDE。平台初始化失败会使 Pod 启动失败，错误可在 Pod 日志或 `/notebook_init.log` 查看。用户自己的 `/mnt/<用户名>/init.sh` 仍以后台方式执行，日志在 `/init.log`。

需要 SSH 时，为每个 Notebook 准备独立凭据；推荐公钥认证。管理员在对应 Notebook 命名空间建立 Secret，把 `authorized_keys` 文件挂载到 `/run/notebook-credentials`，并在 Notebook 环境变量设置：

```text
NOTEBOOK_SSH_PUBLIC_KEY_FILE=/run/notebook-credentials/authorized_keys
```

现有挂载语法为 `my-notebook-ssh(secret):/run/notebook-credentials`，其中 `my-notebook-ssh` 是该 Notebook 专用 Secret 名称。Secret 由管理员按项目隔离，不能跨用户共享。私钥始终留在用户客户端。SSH 端口由平台分配，连接时使用平台显示的外部地址和 SSH 端口。

确需密码认证时，可以改用 `NOTEBOOK_ROOT_PASSWORD_FILE=/run/notebook-credentials/password`。密码至少 16 字符、单行；禁止空密码。兼容 `NOTEBOOK_ROOT_PASSWORD` 直接注入，但它会出现在 Pod 环境和平台数据中，不建议使用。文件和直接值不能同时设置。密码文件错误、密钥校验失败或系统密码更新失败均不会继续启动 SSH。不启用 SSH 时无需设置这些变量。

先重新构建并验证四种企业 Notebook 镜像，再更新平台的默认镜像清单。旧镜像不会因后端代码更新自动获得这些变更；本地回归不代替目标集群中的 SSH、公钥登录和 Notebook 业务测试。

## 方法1：Dockerfile构建

jupyter 镜像的构建脚本：[build.sh](build.sh)。

vscode 镜像的构建目录：[theia](../theia)。

现在默认使用的镜像为
```
# notebook使用的镜像
NOTEBOOK_IMAGES=[
    ['modelone/notebook:vscode-ubuntu-cpu-base', 'vscode（cpu）'],
    ['modelone/notebook:vscode-ubuntu-gpu-base', 'vscode（gpu）'],
    ['modelone/notebook:jupyter-ubuntu-cpu-base', 'jupyter（cpu）'],
    ['modelone/notebook:jupyter-ubuntu-gpu-base','jupyter（gpu）'],
    ['modelone/notebook:jupyter-ubuntu-bigdata', 'jupyter（bigdata）'],
    ['modelone/notebook:jupyter-ubuntu-machinelearning', 'jupyter（machinelearning）'],
    ['modelone/notebook:jupyter-ubuntu-deeplearning', 'jupyter（deeplearning）'],
]
```
## 方法2，直接commit容器

也可以直接run一个容器，然后安装插件后将容器commmit成镜像。
```
# 启动jupyter
docker run --name jupyter -p 3000:3000 -d modelone/notebook:jupyter-ubuntu-cpu-base jupyter lab --notebook-dir=/ --ip=0.0.0.0 --no-browser --allow-root --port=3000 --NotebookApp.token='' --NotebookApp.password='' --NotebookApp.allow_origin='*'

# 启动vscode
docker run --name vscode -p 3000:3000 -d modelone/notebook:vscode-ubuntu-cpu-base node /home/theia/src-gen/backend/main.js /home/project --hostname=0.0.0.0 --port=3000

```
然后访问 http://xx.xx.xx.xx:3000/ ， web界面操作，安装notebook插件，安装pip/apt环境等。环境完整后，再使用如下命令commit成镜像。
```
docker commit notebook modelone/notebook:jupyter-ubuntu-cpu-base-1
```

# 修改配置文件

config.py中 NOTEBOOK_IMAGES 变量为notebook可选镜像。更新此变量即可。


# 其他类型的notebook

所有可提供在线编辑功能的web服务都可以定义为notebook。开发代码已提供对外，需要满足几个条件，可配置url前缀，用来区分不同的notebook。
