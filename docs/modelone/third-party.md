# modelOne 第三方软件清单

运行 `python3 scripts/compliance_inventory.py` 生成 `dist/modelone/compliance/dependencies.json`、`frontend-sbom.cdx.json`（CycloneDX 1.5）、原 LICENSE 副本和已安装前端依赖的 LICENSE/NOTICE 证据。清单按三个锁文件记录包名、版本和声明许可证。

主要组成包括 React、Ant Design、Webpack、Monaco Editor、Flask、Flask-AppBuilder、SQLAlchemy、Alembic、Kubernetes 客户端及各任务控制器。最终镜像还含基础系统、数据库客户端、GPU 库及模型框架，应对最终镜像另行生成 SBOM。

`UNKNOWN`、缺失证据以及 Python/系统镜像项必须复核。当前清单不代表完整依赖审计，也不代表所有依赖均适用 MIT。重新构建或更换镜像后重新生成并审核清单。
