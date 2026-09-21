# modelOne 备份与恢复手册

升级前冻结写入，记录版本、迁移 revision、数据库连接目标、持久卷和镜像摘要。对数据库、共享存储及品牌/部署配置做同一时间点的一致性备份；保留数据库加密参数、访问控制和恢复所需凭据。

MySQL 使用受控的客户端配置文件提供连接信息，避免在命令行暴露密码：

```sh
mysqldump --defaults-extra-file=/secure/mysql-client.cnf --single-transaction --routines --triggers --events kubeflow > metadata.sql
sha256sum metadata.sql > metadata.sql.sha256
```

持久存储采用存储系统快照或经过验证的备份工具；不能仅备份应用容器。备份包括 Notebook 项目文件、模型、数据集、Pipeline 归档、资源清单和对应版本镜像。

恢复必须先在隔离实例演练。创建目标数据库后导入 SQL、恢复同一时间点存储与配置，再启动匹配版本的服务。检查账号/权限、任务记录、样本文件和一次实际任务；通过后才安排生产切换。

升级失败时优先保留现场日志和失败库副本，再按已验证的恢复流程切回。恢复会覆盖目标实例数据，正式操作需要明确目标和维护窗口。本项目尚未在企业环境执行备份恢复演练。

自动化工具：`scripts/backup_modelone.py --client-config <文件> --output <备份.sql>` 创建备份和 SHA-256；`scripts/restore_modelone.py --client-config <文件> --database <空恢复库> --backup <备份.sql>` 先校验，增加 `--apply` 才导入。恢复工具拒绝覆盖非空数据库。客户端配置须为 600 权限。这两个工具尚未进行真实 MySQL 演练。
