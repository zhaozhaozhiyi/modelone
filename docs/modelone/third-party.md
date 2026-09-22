# modelOne 第三方软件清单

运行 `python3 scripts/compliance_inventory.py` 生成 `dist/modelone/compliance/dependencies.json`、`frontend-sbom.cdx.json`（CycloneDX 1.5）、原 LICENSE 副本和已安装前端依赖的 LICENSE/NOTICE 证据。清单按三个锁文件记录包名、版本和声明许可证。

主要组成包括 React、Ant Design、Webpack、Monaco Editor、Flask、Flask-AppBuilder、SQLAlchemy、Alembic、Kubernetes 客户端及各任务控制器。最终镜像还含基础系统、数据库客户端、GPU 库及模型框架，应对最终镜像另行生成 SBOM。

镜像盘点使用 Docker 与 Syft 1.51.1，安装后对已缓存的实际交付镜像运行：

```sh
python3 scripts/image_compliance.py \
  --image <企业镜像名或本地sha256摘要> \
  --output dist/modelone/compliance-images/<新目录>
```

工具先解析本地镜像不可变 ID，再扫描最终文件系统；不启动容器、不拉取或推送镜像。`config/modelone-syft.yaml` 关闭更新检查和远程包信息补全。输出包括 Syft 原生包证据、CycloneDX 1.5、SPDX 2.3、原许可证副本、许可证/NOTICE/系统版权文件、来源路径与 SHA-256 映射、逐包待审列表以及所有交付文件的校验和。原许可证必须在镜像 `/usr/share/licenses/modelone/LICENSE` 内与源码逐字一致，否则不会发布结果。此约束用于 modelOne 自有镜像；第三方数据库、控制器和 GPU 镜像应按各自许可证另行收集。

输出目录必须不存在，扫描失败不会留下看似完整的交付目录。报告目录为 700，文件为 600；原始镜像环境变量与构建历史不写入交付 SBOM。包元数据、内部路径和版权文件仍需按交付范围审查，不能直接作为产品公开资源。许可证按原始字节保存，不修改第三方版权声明。

包记录包含嵌套或随其他库附带的依赖，因此数量可能高于 Python 包管理器的直接安装列表。`review.json` 将缺失许可证声明和未关联许可证文件分别列出；所有记录均保留 `reviewRequired: true`。发现文件不代表自动确认许可证义务。超过 2 MiB 的文本、不识别的二进制、另行挂载的模型/数据、构建阶段未进入最终镜像的依赖仍需补证；这不是漏洞扫描。最终企业镜像、每个交付架构和版本都应重新盘点，前端锁文件证据仍须保留以覆盖编译后无法从镜像反推的 JavaScript 依赖。

CI 固定 Syft 版本并扫描当次构建的前端镜像，将证据随检查产物归档；本地四项回归验证镜像来源、原许可证一致性、文件路径安全和证据关联范围。后端及任务镜像需在企业构建流水线中执行同一命令，不以本地验证镜像的报告替代。

`UNKNOWN`、缺失证据以及 Python/系统镜像项必须复核。当前清单不代表完整依赖审计，也不代表所有依赖均适用 MIT。重新构建或更换镜像后重新生成并审核清单。
