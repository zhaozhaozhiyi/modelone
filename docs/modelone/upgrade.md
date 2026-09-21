# modelOne 升级迁移手册

升级前备份数据库、业务持久卷、配置与旧镜像；冻结写入后记录当前迁移版本。在隔离恢复库先执行 `myapp db upgrade`，核对迁移 `modelone_brand_20260921` 的结果，再安排正式升级。

后续迁移 `modelone_brand_links_20260921` 补充镜像文档、数据集来源和预览图、Pipeline 卡片参数等字段。已安装早期品牌基线的环境也需执行到此版本。两次迁移均不修改作业名称和主键。

迁移通过数据库结构检查跳过不存在的可选表，只修改允许列表中的展示字段和资源地址。保留业务名称、API 路径、挂载路径和 CRD，不批量重命名作业。SQL 错误会中止升级；重复执行品牌转换应不再产生修改。

镜像和资源前缀使用统一品牌配置。知识库例外路径由 `pipeline/example/gpt/cube-studio.csv` 迁到 `pipeline/example/gpt/modelone.csv`：必须把新文件同步到实际共享存储并重建知识索引。历史平台问答保留原内部 chat 名称以兼容原 URL，新安装使用 modelone。

导出数据可先运行 `python3 scripts/migrate_modelone.py <暂存目录>` 预览资源替换，确认后增加 `--apply`；工具逐文件保存 `.bak`，不会处理源码树或许可证，也不声称完成任意历史数据清理。

品牌文本无法可靠反向还原，Alembic downgrade 会明确报错；需要回退时恢复升级前完整数据库备份与相应旧镜像。SQLite 回归已覆盖幂等、可选表、JSON、空值及标识保护；真实 MySQL 升级和全新安装仍需验收。

内部兼容保留项：cubestudio SDK、已有 conda 环境名、数据库表名、容器与存储目录、kubeflow-dashboard 服务名、历史认证配置以及已存在的任务/API 标识。许可证和内部技术资料允许保留原项目名称，不作为平台产品内容展示。
