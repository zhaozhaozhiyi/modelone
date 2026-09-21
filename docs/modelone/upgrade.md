# modelOne 升级迁移手册

升级前备份数据库、业务持久卷、配置与旧镜像；冻结写入后记录当前迁移版本。在隔离恢复库先执行 `myapp db upgrade`，核对迁移 `modelone_brand_20260921` 的结果，再安排正式升级。

Docker Compose 升级时保留现有 `MYSQL_SERVICE`、`MODELONE_MYSQL_ROOT_PASSWORD`、`MODELONE_MYSQL_PASSWORD` 和 `REDIS_PASSWORD`，不要运行生成器覆盖它们；只在首次安装生成 Compose 凭据。Kubernetes 升级时保留 `modelone-infrastructure`、`modelone-mysql` 和 `modelone-auth` Secret 及其数据卷。若旧 MySQL 仍使用 root 连接或没有 `modelone` 应用账号，先在维护窗口创建最小权限账号或将 `MYSQL_SERVICE` 指向现有受控账号，再滚动升级后端。旧持久卷不会因 Secret 名称改变而自动重置密码。

后续迁移 `modelone_brand_links_20260921` 补充镜像文档、数据集来源和预览图、Pipeline 卡片参数等字段。已安装早期品牌基线的环境也需执行到此版本。两次迁移均不修改作业名称和主键。

迁移通过数据库结构检查跳过不存在的可选表，只修改允许列表中的展示字段和资源地址。保留业务名称、API 路径、挂载路径和 CRD，不批量重命名作业。SQL 错误会中止升级；重复执行品牌转换应不再产生修改。

镜像和资源前缀使用统一品牌配置。知识库例外路径由 `pipeline/example/gpt/cube-studio.csv` 迁到 `pipeline/example/gpt/modelone.csv`：必须把新文件同步到实际共享存储并重建知识索引。历史平台问答保留原内部 chat 名称以兼容原 URL，新安装使用 modelone。

导出数据可先运行 `python3 scripts/migrate_modelone.py <暂存目录>` 预览资源替换，确认后增加 `--apply`；工具逐文件保存 `.bak`，不会处理源码树或许可证，也不声称完成任意历史数据清理。

品牌文本无法可靠反向还原，Alembic downgrade 会明确报错；需要回退时恢复升级前完整数据库备份与相应旧镜像。SQLite 回归和本地隔离 MySQL 8.0.46 样本测试已覆盖幂等、可选表、JSON、空值及标识保护，样本备份恢复通过；企业全量升级和安装仍需验收。

内部兼容保留项：cubestudio SDK 名称、已有 conda 环境名、数据库表名、容器与存储目录、kubeflow-dashboard 服务名以及已存在的任务/API 路径。许可证和内部技术资料允许保留原项目名称，不作为平台产品内容展示。认证凭据必须按下述规则升级，保留路径不代表接受旧的免验证登录方式。

## 认证凭据升级

先在隔离恢复环境按安装手册生成独立会话/JWT 密钥，并以私密环境文件或 Kubernetes Secret 分发给所有后端进程。首次切换密钥会使原会话和旧令牌失效，安排重新登录；以后重启必须保留这些密钥。生产启用 HTTPS，使用 `STAGE=prod`。

`/login/?username=...`、以用户名作为 Authorization，以及 GET/查询参数 `/login/api/` 已禁用。SDK 使用用户资料中的新 API 令牌，可传两段短令牌、完整 JWT 或 `Bearer <JWT>`；默认有效期 30 天，可用 `MODELONE_API_TOKEN_TTL_SECONDS` 在 60 秒至一年范围内配置。原固定密钥及缺少声明的令牌不被接受。令牌登录只允许 POST JSON，不能传用户组织参数改动账号。

已有管理员和哈希密码保持不变，初始化不重置密码。历史明文密码不再支持登录；管理员须在切换前通过受控账号管理重设这些账号的密码，并核实无弱密码遗留。`MODELONE_ADMIN_PASSWORD` 只负责空库初始化，不能用它恢复已有管理员密码。

重新构建数据集、模型下载、模型登记和服务部署启动器镜像，移除调试跟踪；重新生成排队工作流及受影响 Pod。新 Pipeline/调试任务自动得到 `SECRET`，其任务令牌仅限数据集、项目、模型登记与推理 API，仍受用户原有角色权限约束。令牌不能创建浏览器会话或访问用户管理。已有运行实例不会自动获得新凭据，任务持续时间须小于令牌有效期，过期后需要受控更新或重启。

隔离容器已验证正常账号登录、失效账号和令牌拒绝、重复初始化保留密码；真实集群任务、企业 SSO、升级全量数据与密钥轮换仍需验收。此版本未提供逐令牌撤销清单；停用账号会阻止其会话和令牌，轮换 JWT 密钥会使所有已有 API/任务令牌失效。
