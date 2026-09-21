# modelOne 节点批量维护

本工具按节点顺序执行一个明确选择的阶段，等待远端完成后才报告结果。任何节点失败都会让最终退出码非零，并继续处理剩余节点。控制端需要 Python 3、OpenSSH；节点需要 Bash、对应阶段使用的工具及非交互管理权限。节点主机密钥必须已通过企业可信方式登记在 `known_hosts`，SSH 使用密钥或 agent 认证。

准备换行分隔的 IP 列表，支持 IPv4/IPv6、空行和 `#` 注释。所有地址在连接前校验。另建权限为 600 的 JSON 文件，例如只检测 Docker：

```json
{"STAGE": "11"}
```

```sh
chmod 600 /private/path/nodes.json
export MODELONE_NODE_IPS_FILE=/private/path/nodes.txt
export MODELONE_SSH_USER=operator
export MODELONE_NODE_CONFIG_FILE=/private/path/nodes.json
bash install/kubernetes/rancher/批量ssh/batch-ssh.sh
```

| STAGE | 操作 | 配置 |
| --- | --- | --- |
| 1 | 在全新 Ubuntu 节点安装 Docker，写入 daemon 配置 | 执行前审核 init.sh 中版本、磁盘与镜像源 |
| 11 | 检测 Docker | 无 |
| 2 | 安装 NFS 客户端并挂载 /data/nfs | MODELONE_NFS_SERVER、MODELONE_NFS_EXPORT |
| 22 | 检测 NFS | 无 |
| 3 | 从共享安装目录导入 Rancher 镜像 | MODELONE_INSTALL_ROOT |
| 33 | 检测 Rancher 镜像 | 无 |
| 4 | 查看网卡 IPv4 地址 | 可选 MODELONE_NODE_INTERFACE，默认 eth0 |
| 44 | 加入 Rancher 工作节点 | RANCHER_SERVER_URL、RANCHER_AGENT_TOKEN、RANCHER_AGENT_CA_CHECKSUM；可选 RANCHER_AGENT_IMAGE、MODELONE_NODE_INTERFACE |

配置值均为 JSON 字符串。加入集群的短期 Token 和 CA 校验值只放入私密 JSON，不写进源码、节点列表或命令行。整个脚本与配置经 SSH 标准输入传输，不在节点上复制凭据文件；控制台只报告节点结果，不转发可能含凭据的原始远端输出。失败后到该节点的服务日志检查原因，再仅对失败节点重试。Rancher agent 自身保存和使用 Token 的行为仍需企业运维管理。

当前验证使用本地替代 SSH/Docker 进程，检查顺序、失败传播、配置引用及输入拒绝；未连接任何实际节点。执行安装或加入集群前，应在目标发行版的隔离测试节点验证所选阶段。
