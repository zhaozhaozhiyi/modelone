# modelOne 安装部署手册

## 准备与构建

准备 Python 3.11（构建和检查工具）、Node.js 22、Docker Compose、kubectl、SQLAlchemy、PyYAML 和 PyJWT 2.8–2.x。基础镜像和 CI 使用 Node.js 22；运行容器仍使用其 Dockerfile 指定的 Python 版本。先填写 `config/modelone.json`；企业差异也可使用 `MODELONE_*` 环境变量覆盖。

本地账号登录已加固；生产部署仍需处理[安全检查记录](security-review.md)中的企业认证、基础设施和目标环境验收项。

```sh
python3 scripts/generate_brand.py
python3 scripts/test_modelone.py
python3 scripts/test_modelone_auth.py
python3 scripts/test_modelone_notebook.py
python3 scripts/test_modelone_nodes.py
python3 scripts/test_modelone_resources.py
python3 scripts/test_modelone_image_bundle.py
for app in frontend vision visionPlus; do
  npm ci --prefix "myapp/$app" --legacy-peer-deps --no-audit --no-fund
  npm run build --prefix "myapp/$app"
done
python3 scripts/brand_scan.py --built
python3 scripts/resource_inventory.py
python3 scripts/compliance_inventory.py
python3 scripts/render_deployment.py --release
python3 scripts/brand_scan.py \
  --artifact dist/modelone/compose.yaml \
  --artifact dist/modelone/kubernetes.yaml \
  --artifact dist/modelone/brand.json
```

`--release` 要求企业仓库、完整 HTTP(S) 资源 CDN、版权方、帮助、支持、用户协议和隐私地址配置；相对资源路径、含凭据的 URL 和错误仓库格式会被拒绝，不等于完整发布验收。清单输出在 `dist/modelone`；未提供企业配置时可省略此参数生成开发预览。产物扫描只针对 Compose、Kubernetes 和品牌清单，资源迁移报告保留原始来源作为审计证据，不应作为运行时交付目录直接发布。

镜像仓库配置格式为 `registry.example.com/team`，不要附加 `/modelone`。渲染器将工作负载镜像写为 `<仓库>/modelone/<镜像>:<标签>`。Compose 直接使用源文件时，`MODELONE_IMAGE_PREFIX` 必须包含尾随 `/`；后端的 `MODELONE_IMAGE_REGISTRY` 不包含尾随命名空间。环境变量覆盖通过渲染器写入容器；直接使用源 Compose 时以挂载的 JSON 配置为准。

## 镜像与资源

清单中的 `pending` 项尚未同步，不能用不存在的 `modelone/` 默认镜像启动生产。审核清单并登录仓库后，可运行 `python3 scripts/resource_inventory.py --copy-images`；需要安装 skopeo，它保留多架构镜像并比对摘要。资源可用 `--download-assets <暂存目录>` 下载，工具记录 SHA-256；上传企业存储或打入离线包后需逐项验证访问与校验和。本地下载状态 `downloaded` 不满足发布条件。工具每项保存进度，可用 `--resume <报告>` 继续操作；更换来源、目标或路径后不会复用旧校验记录。上传后运行 `python3 scripts/resource_inventory.py --resume dist/modelone/resource-inventory.json --verify-targets --require-complete`，重新读取企业镜像摘要和 CDN 文件并比对；不存在、内容不同、跳转回原存储或仍待迁移的资源都会使门禁失败。已有报告中的 `verified` 不能跳过当次目标验证。盘点包含历史文档和示例引用，需要按企业保留清单筛选。

当前清单去重后为 147 个镜像、939 个资源：已纳入 Argo 控制器镜像，分离语音 CSV 的 URL 与转写文本，并将智能问答中的 4 张示例图展开为实际地址。教程文件的目标路径与页面使用的 `tutorial-pipeline.mp4`、`tutorial-job-template.mp4` 一致。清单保存原始来源供追溯；修改文件名不会修改媒体内容，视频和图片还需检查画面中的旧品牌，替换为正式素材后才能对外发布。

初始化任务模板中的帮助和镜像说明入口使用配置的帮助中心；尚未配置时隐藏入口，避免跳转到不存在的本地仓库路径。第三方工具的帮助链接仍指向其原文档。

`assetBaseUrl` 应是浏览器和任务容器均可访问的完整 HTTP(S) 地址。默认 `/static/assets/modelone/` 只用于静态品牌和本地页面，不能直接当作容器中 wget/curl 的完整 URL。外部模型、教程和数据未打入本次代码改造，安装前必须准备好。

## Docker Compose

渲染文件中的挂载路径指向当前源码目录，不是可移机使用的独立安装包。先构建并推送企业后端和前端镜像。后端构建参数 `MODELONE_IMAGE_PREFIX` 当前作为前缀使用，传入时需包含尾随 `/`；基础镜像必须已同步。

也可通过 `MODELONE_BACKEND_BASE_IMAGE` 指定完整的企业后端基础镜像，通过 `MODELONE_NGINX_IMAGE` 指定企业 Nginx 镜像。构建会清理基础镜像中已有的产品静态目录后复制当前产物，保留 PWA 清单，并在 `/usr/share/licenses/modelone/LICENSE` 附带原许可证。后端镜像内包含 Docker 运行配置，部署时仍可用挂载文件覆盖。

```sh
python3 scripts/init_modelone_secrets.py --output .modelone-secrets/compose.env
docker compose --env-file .modelone-secrets/compose.env -f dist/modelone/compose.yaml config --quiet
docker compose --env-file .modelone-secrets/compose.env -f dist/modelone/compose.yaml up -d
```

密钥生成只执行一次；文件权限为 600，默认目录已从 Git 与镜像构建上下文排除。通过受保护方式保存和分发该文件，不打印完整 Compose 配置或把密钥写入品牌 JSON。生成器拒绝覆盖已有文件，重启或新增副本必须复用同一套会话/JWT 密钥。

`MODELONE_SECRET_KEY` 和 `MODELONE_JWT_KEY` 至少 32 字符且不同；`MODELONE_ADMIN_PASSWORD` 仅在初次创建 admin 时使用，至少 16 字符。已有管理员不会被重置。也可通过 `<变量名>_FILE` 向后端读取挂载文件；使用该方式时调整 Compose，移除对应直接环境变量的必填声明并挂载文件，不同时设置两种形式。

生成的 Compose 文件同时包含独立的 MySQL root/应用账号和 Redis 密码；不要改回示例值。确认持久化路径、配置 kubeconfig 并限制服务监听范围。默认只在本机 `127.0.0.1:8080` 暴露前端，可通过 `MODELONE_HTTP_BIND` 和 `MODELONE_HTTP_PORT` 配置入口。默认使用 `STAGE=prod`；生产会话 cookie 默认要求 HTTPS，仅隔离 HTTP 测试可显式设置 `MODELONE_COOKIE_SECURE=false`。平台计算任务须连接 Kubernetes。

## Kubernetes

渲染器保留既有命名空间、服务名、选择器和 CRD，添加 modelone 应用标签和品牌 ConfigMap。企业环境需预建数据库、存储、控制器、镜像拉取 Secret 以及 kubeconfig；所需资源参照既有 install/kubernetes 基础设施目录。

```sh
python3 scripts/init_modelone_secrets.py --kubernetes-new-install --output .modelone-secrets/kubernetes-secrets.json
kubectl apply -f .modelone-secrets/kubernetes-secrets.json
kubectl apply --dry-run=server -f dist/modelone/kubernetes.yaml
kubectl apply -f dist/modelone/kubernetes.yaml
kubectl -n infra rollout status deployment/kubeflow-dashboard
```

新安装的 Secret 清单包含 `modelone-auth`、`modelone-infrastructure`（应用数据库 URL 和 Redis 密码）以及 `modelone-mysql`（MySQL 初始化密码）。先应用该清单，再启动 MySQL、Redis 和后端。多个副本及上述进程共用同一套密钥；前端不需要读取认证 Secret。生成文件也是私密数据，需纳入企业密钥备份。不要对已有安装重新生成密钥，升级操作见[升级迁移](upgrade.md)。

已有数据库或 Redis 不要使用 `--kubernetes-new-install` 覆盖凭据。将现有 `MYSQL_SERVICE` 和 Redis 密码写入权限为 600 的私密 JSON，再运行 `python3 scripts/init_modelone_secrets.py --infrastructure-from-json <文件> --output .modelone-secrets/modelone-infrastructure.json`，并单独生成或恢复 `modelone-auth`。已有自建 MySQL 还需创建 `modelone-mysql` Secret，使 MySQL Pod 的 root 初始化变量与原持久卷凭据一致；不要对已有数据卷重新初始化。

正式域名和 TLS 证书需要在实际入口网关配置并验证。当前未配置目标集群，尚未执行上述集群命令。平台和 Rancher 镜像计划、完整归档校验与离线导入流程见[离线安装](../../install/kubernetes/offline.md)。完全离线安装还需所有第三方镜像、软件包及模型文件的闭环验证。

## 本地隔离容器验证

先完成镜像构建；以下测试只使用本机已有镜像，不拉取或推送远程仓库。临时容器只公开随机回环端口，测试结束清理自己的容器、临时数据和网络，不操作已有环境。

```sh
python3 scripts/test_modelone_mysql.py --image <已缓存的MySQL-8.0镜像>
python3 scripts/test_modelone_frontend_image.py --image <本地构建的前端镜像>
python3 scripts/test_modelone_app.py --backend-image <本地构建的后端镜像> --mysql-image <已缓存的MySQL-8.0镜像> --redis-image <已缓存的兼容Bitnami配置的Redis镜像>
```

MySQL 测试额外需要 PyMySQL、mysql 和 mysqldump 客户端；测试实例使用原生密码认证以兼容旧客户端，不改变企业服务器认证配置。应用测试使用临时随机凭据和本地开发启动方式，验证空库初始化、健康/品牌页面、正确与错误密码、CSRF、禁止自动注册、令牌签名和有效期、任务用途限制、停用账号及重复管理员初始化；它不运行 Notebook、训练或推理任务，也不验证企业 SSO。前端测试检查三个入口的实际 HTTP 静态响应，并放入测试 source map 验证拒绝规则。

报告为 `dist/modelone/mysql-validation.json`、`frontend-image-validation.json` 和 `app-smoke-validation.json`。通过后仍须对正式企业镜像、目标数据库和 Kubernetes 集群复测。
