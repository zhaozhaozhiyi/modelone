# modelOne 安装部署手册

## 准备与构建

准备 Python 3.11（构建和检查工具）、Node.js 22、Docker Compose、kubectl、SQLAlchemy、PyYAML、PyJWT 2.8–2.x 和 Flask 2.3–3.x（品牌接口检查）。基础镜像和 CI 使用 Node.js 22；运行容器仍使用其 Dockerfile 指定的 Python 版本。先填写 `config/modelone.json`；企业差异也可使用 `MODELONE_*` 环境变量覆盖。

品牌配置中的 `primaryColor`、`secondaryColor`、`loginBackgroundColor`、`loginSurfaceColor` 和 `fontFamily` 同时供后端登录/错误页面、主控制台及两个独立编排器使用。正式 Logo 替换 `logoUrl`、`logoReverseUrl` 和 `faviconUrl` 后，重新运行 `python3 scripts/generate_brand.py`；该命令会同步三个前端的运行时品牌脚本和 PWA `manifest.json`，随后重建三个前端。不要只替换某一个入口的静态文件。

连接后端时，三个入口通过 `/myapp/brand.js` 读取部署配置，并将 PWA 安装信息切换到对应的 `/myapp/manifest/<app>.json`。修改品牌环境变量并重启后端后，浏览器页面与安装清单使用同一配置；未连接后端的静态页面继续使用构建时的 `brand-config.js` 和 `manifest.json`。需要同步静态回退内容时仍须重新生成并构建前端。图标类型按配置 URL 的文件扩展名确定，支持 PNG、ICO、SVG、WebP 等格式；未知扩展名交由浏览器识别，不假定为 SVG。

前端代理自身产生的 500/502/503/504 页面也使用统一品牌配置，并保留原始 HTTP 状态码。`generate_brand.py` 生成随镜像提供的默认错误页；`render_deployment.py` 另生成 `frontend-errors/` 和 Kubernetes `modelone-error-pages` ConfigMap，以部署配置覆盖镜像默认值。品牌变化后需重新渲染并交付这些文件；仅重启后端不会更新代理的静态错误页。默认 Logo 和 favicon 由前端 `/static/assets/modelone/` 独立提供；自定义资产应打入前端同一路径或放在可独立访问的企业 CDN，避免依赖故障中的后端。应用自身返回的 JSON/HTML 错误保持原样。

## 代码仓库

企业 Git 仓库创建完成后，在工作树中先做一次预览，再显式应用远端配置。工具不会替换已有 `origin`，也不会向 `upstream` 推送；已有 `origin` 只有在明确传入 `--replace-origin` 时才会被替换。URL 不应内嵌账号或密码。

```sh
MODELONE_ORIGIN_URL='<企业 Git 仓库地址>'
MODELONE_UPSTREAM_URL='<原项目只读仓库地址>'
python3 scripts/configure_modelone_remotes.py \
  --origin "$MODELONE_ORIGIN_URL" \
  --upstream "$MODELONE_UPSTREAM_URL"
python3 scripts/configure_modelone_remotes.py \
  --origin "$MODELONE_ORIGIN_URL" \
  --upstream "$MODELONE_UPSTREAM_URL" \
  --apply
git remote -v
```

应用后，`origin` 指向企业仓库，`upstream` 的 fetch URL 指向原始仓库且 push URL 为 `DISABLED`。未收到企业地址时不要使用示例地址，也不要创建正式发布标签。

本地账号登录已加固；生产部署仍需处理[安全检查记录](security-review.md)中的企业认证、基础设施和目标环境验收项。

```sh
python3 scripts/generate_brand.py
python3 scripts/test_modelone.py
python3 scripts/test_modelone_auth.py
python3 scripts/test_modelone_notebook.py
python3 scripts/test_modelone_nodes.py
python3 scripts/test_modelone_resources.py
python3 scripts/test_modelone_image_bundle.py
python3 scripts/test_modelone_manifests.py
for app in frontend vision visionPlus; do
  npm ci --prefix "myapp/$app" --legacy-peer-deps --no-audit --no-fund
  npm run build --prefix "myapp/$app"
done
python3 scripts/brand_scan.py --built
node scripts/test_modelone_browser_brand.cjs
python3 scripts/resource_inventory.py
python3 scripts/compliance_inventory.py
python3 install/kubernetes/all_image.py \
  --manifest-root install/kubernetes \
  --output dist/modelone/platform-images
python3 scripts/render_deployment.py \
  --release \
  --image-plan dist/modelone/platform-images/images.json
python3 scripts/rewrite_deployment_images.py \
  --plan dist/modelone/platform-images/images.json \
  --source-root install/kubernetes \
  --output-dir dist/modelone/platform-manifests/kubernetes
python3 scripts/brand_scan.py \
  --artifact dist/modelone/compose.yaml \
  --artifact dist/modelone/kubernetes.yaml \
  --artifact dist/modelone/brand.json \
  --artifact dist/modelone/frontend-errors \
  --artifact dist/modelone/platform-manifests/kubernetes
```

`--release` 要求企业仓库、完整 HTTP(S) 资源 CDN、版权方、帮助、支持、用户协议和隐私地址配置，并且必须传入由完整部署清单生成、仓库地址与当前品牌配置一致且所有目标镜像都位于该仓库命名空间下的 `--image-plan`；相对资源路径、含凭据的 URL 和错误仓库格式会被拒绝，不等于完整发布验收。正式环境可通过 `MODELONE_PUBLIC_DOMAIN` 和 `MODELONE_TLS_SECRET_NAME`（或 `config/modelone.json` 的 `publicDomain`、`tlsSecretName`）配置入口域名和 TLS Secret；重写发布清单时，Gateway、VirtualService 和 Ingress 会使用该域名，主 Gateway 会追加 HTTPS 443 服务，Ingress 会生成对应的 `spec.tls`。只配置域名会保留 HTTP 端口，TLS Secret 必须和域名同时配置。清单输出在 `dist/modelone`；未提供企业配置时可省略此参数生成开发预览。产物扫描只针对 Compose、Kubernetes 和品牌清单，资源迁移报告保留原始来源作为审计证据，不应作为运行时交付目录直接发布。

镜像仓库配置格式为 `registry.example.com/team`，不要附加 `/modelone`。渲染器将工作负载镜像写为 `<仓库>/modelone/<镜像>:<标签>`。发布前先生成镜像计划并把它传给渲染器，Compose、Kubernetes 和离线 Argo 产物才会统一使用企业目标镜像。`install/kubernetes/all_image.py` 和 Rancher 计划生成器优先读取 `MODELONE_IMAGE_REGISTRY`，未设置时读取 `config/modelone.json`。Compose 直接使用源文件时，`MODELONE_IMAGE_PREFIX` 必须包含尾随 `/`；后端的 `MODELONE_IMAGE_REGISTRY` 不包含尾随命名空间。环境变量覆盖通过渲染器写入容器；直接使用源 Compose 时以挂载的 JSON 配置为准。

发布清单树包含 Kustomize generator 明确引用的本地文件（`files`、`envs`），包括主平台的 Python 配置和启动脚本；源目录和输出目录必须互不包含，引用的文件必须位于源目录内。可用 `kubectl kustomize dist/modelone/platform-manifests/kubernetes/cube/overlays` 和训练控制器的 `kubeflow/train-operator/manifests/overlays/standalone` 路径检查构建。主平台实际部署仍使用 `render_deployment.py` 生成的 `kubernetes.yaml`，其中包含企业品牌 ConfigMap 和运行环境。

## 镜像与资源

清单中的 `pending` 项尚未同步，不能用不存在的 `modelone/` 默认镜像启动生产。审核清单并登录仓库后，可运行 `python3 scripts/resource_inventory.py --copy-images`；需要安装 skopeo，它保留多架构镜像并比对摘要。资源可用 `--download-assets <暂存目录>` 下载，工具记录 SHA-256；上传企业存储或打入离线包后需逐项验证访问与校验和。本地下载状态 `downloaded` 不满足发布条件。工具每项保存进度，可用 `--resume <报告>` 继续操作；更换来源、目标或路径后不会复用旧校验记录。上传后运行 `python3 scripts/resource_inventory.py --resume dist/modelone/resource-inventory.json --verify-targets --require-complete`，重新读取企业镜像摘要和 CDN 文件并比对；不存在、内容不同、跳转回原存储或仍待迁移的资源都会使门禁失败。已有报告中的 `verified` 不能跳过当次目标验证。盘点包含历史文档和示例引用，需要按企业保留清单筛选。

当前清单去重后为 147 个镜像、943 个资源：已纳入 Argo 控制器镜像，分离语音 CSV 的 URL 与转写文本，将智能问答中的 4 张示例图展开为实际地址，并纳入 MNIST 示例的 4 个数据文件。教程文件的目标路径与页面使用的 `tutorial-pipeline.mp4`、`tutorial-job-template.mp4` 一致。清单保存原始来源供追溯；修改文件名不会修改媒体内容，视频和图片还需检查画面中的旧品牌，替换为正式素材后才能对外发布。

初始化任务模板中的帮助和镜像说明入口使用配置的帮助中心；尚未配置时隐藏入口，避免跳转到不存在的本地仓库路径。第三方工具的帮助链接仍指向其原文档。

`assetBaseUrl` 应是浏览器和任务容器均可访问的完整 HTTP(S) 地址。默认 `/static/assets/modelone/` 只用于静态品牌和本地页面，不能直接当作容器中 wget/curl 的完整 URL。发布门禁会拒绝原项目托管主机、旧第三方数据主机及其重定向目标；外部模型、教程和数据未打入本次代码改造，安装前必须准备好企业资源地址。

MNIST 示例使用 `MODELONE_MNIST_BASE_URL`（或 `MODELONE_ASSET_BASE_URL`）拼接 `/datasets/mnist/`，不会回退到旧公共主机；资源同步清单中的四个压缩文件必须先上传到该路径，再启用对应任务模板。

## Docker Compose

开发预览渲染文件会挂载当前源码目录；`--release` 生成的 Compose 使用已发布的后端/前端镜像和命名数据卷（应用数据与 MySQL 数据），不依赖源码绝对路径。交付时须保留 Compose 同目录的 `frontend-errors/`，并准备 kubeconfig，或通过 `MODELONE_KUBECONFIG` 指定受保护的 kubeconfig 文件。先构建并推送企业后端和前端镜像。后端构建参数 `MODELONE_IMAGE_PREFIX` 当前作为前缀使用，传入时需包含尾随 `/`；基础镜像必须已同步。

也可通过 `MODELONE_BACKEND_BASE_IMAGE` 指定完整的企业后端基础镜像，通过 `MODELONE_NGINX_IMAGE` 指定企业 Nginx 镜像。构建会清理基础镜像中已有的产品静态目录后复制当前产物，保留 PWA 清单，并在 `/usr/share/licenses/modelone/LICENSE` 附带原许可证。后端镜像内包含 Docker 运行配置，部署时仍可用挂载文件覆盖。

```sh
python3 scripts/init_modelone_secrets.py --output .modelone-secrets/compose.env
docker compose --env-file .modelone-secrets/compose.env -f dist/modelone/compose.yaml config --quiet
docker compose --env-file .modelone-secrets/compose.env -f dist/modelone/compose.yaml up -d
```

正式 Compose 不会从工作树挂载应用代码、静态资源或任务模板；这些内容已随镜像发布。`MODELONE_KUBECONFIG` 只读挂载到后端容器，不能把 kubeconfig 写入镜像或提交到 Git。

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

可选的 `ingress.yaml` 使用 ingress-nginx：主入口 `/` 指向平台前端，`/grafana/` 指向 Grafana Service 的 8080 端口，`/k8s/dashboard/cluster/` 和 `/minio/` 去掉前缀后转发到各自服务。使用这些入口前需安装对应服务和 Ingress 控制器；标准集群启动脚本仍使用 Istio Gateway。Pipeline 页面由平台前端提供，不再转发到不存在的独立 UI 服务。Docker 和 Kubernetes 前端 Nginx 使用相对首页重定向，保留网关前的 HTTPS 协议。

两套前端代理必须保留浏览器 `Origin`，后端才能拒绝外站及 `null` 来源的令牌登录；不要为 WebSocket 兼容而清空该请求头。生产 HTTPS 入口需由受控网关覆盖 `X-Forwarded-Proto`，并清除客户端传入的 `X-Forwarded-Protocol` 和 `X-Forwarded-Ssl`，避免不同协议头相互冲突。将实际直接连接后端的前端代理 IP 配置到 `MODELONE_TRUSTED_PROXY_IPS`（多个地址用逗号分隔），并随代理副本地址变化更新；默认值仅信任回环地址。限制后端直接访问及代理链来源，避免信任客户端自带的转发头。正式 HTTPS 会话、同源登录和 WebSocket 连接仍须按实际拓扑验收。

正式域名和 TLS 证书需要在实际入口网关配置并验证。`install/kubernetes/ingress.yaml` 包含多个命名空间的兼容入口；启用 `MODELONE_TLS_SECRET_NAME` 时，必须在每个对应命名空间预置同名证书 Secret，或只使用统一 Istio Gateway 入口。当前未配置目标集群，尚未执行上述集群命令。平台和 Rancher 镜像计划、完整归档校验与离线导入流程见[离线安装](../../install/kubernetes/offline.md)。完全离线安装还需所有第三方镜像、软件包及模型文件的闭环验证。

`install/kubernetes/start.sh` 和 `start-with-kubesphere.sh` 只接受已经渲染并通过品牌/镜像扫描的发布清单：默认读取 `../../dist/modelone/kubernetes.yaml` 和 `../../dist/modelone/platform-manifests/kubernetes/argo/install-3.4.3-all.yaml`，并把所有源码 `-f/-k` 引用映射到 `../../dist/modelone/platform-manifests/kubernetes`。也可通过 `MODELONE_RELEASE_DIR`、`MODELONE_KUBERNETES_MANIFEST`、`MODELONE_MANIFEST_ROOT` 和 `MODELONE_ARGO_MANIFEST_DIR` 指定路径。脚本不会直接应用源码中的 Argo 清单或 Kustomize overlay。节点地址通过 `MODELONE_SERVICE_EXTERNAL_IP` 注入工作负载；未设置时使用启动脚本的节点地址参数。

## 本地隔离容器验证

先完成镜像构建；以下测试只使用本机已有镜像，不拉取或推送远程仓库。临时容器只公开随机回环端口，测试结束清理自己的容器、临时数据和网络，不操作已有环境。

```sh
python3 scripts/test_modelone_mysql.py --image <已缓存的MySQL-8.0镜像>
python3 scripts/test_modelone_frontend_image.py --image <本地构建的前端镜像>
python3 scripts/test_modelone_app.py --backend-image <本地构建的后端镜像> --mysql-image <已缓存的MySQL-8.0镜像> --redis-image <已缓存的兼容Bitnami配置的Redis镜像>
python3 scripts/test_modelone_app.py --backend-image <本地构建的后端镜像> --frontend-image <本地构建的前端镜像> --mysql-image <已缓存的MySQL-8.0镜像> --redis-image <已缓存的兼容Bitnami配置的Redis镜像> --output dist/modelone/proxy-validation
python3 scripts/test_modelone_app.py --https --backend-image <本地构建的后端镜像> --frontend-image <本地构建的前端镜像> --mysql-image <已缓存的MySQL-8.0镜像> --redis-image <已缓存的兼容Bitnami配置的Redis镜像> --output dist/modelone/tls-validation
```

MySQL 测试额外需要 PyMySQL、mysql 和 mysqldump 客户端；测试实例使用原生密码认证以兼容旧客户端，不改变企业服务器认证配置。应用测试使用临时随机凭据和本地开发启动方式，验证空库初始化、健康/品牌页面、正确与错误密码、CSRF、禁止自动注册、令牌签名和有效期、任务用途限制、停用账号及重复管理员初始化。传入 `--frontend-image` 后，全部业务 HTTP 检查通过前端入口，额外验证三个产品入口、同源登录成功、外站及 `null` 来源不建立会话、401/404 页面使用部署品牌；可用 `--nginx-config <文件>` 挂载从 Kubernetes ConfigMap 提取的 `default.conf` 复测。默认 HTTP 模式不验证 TLS；所有模式均不运行 Notebook、训练或推理任务，也不验证企业 SSO 或实际浏览器。

前端镜像测试检查三个入口的实际 HTTP 静态响应，并放入测试 source map 验证拒绝规则；它还用同一缓存镜像启动临时 Nginx 回显上游，验证 Origin、Host、认证、Cookie 和 WebSocket 升级头的透传。CI 会对 Docker 默认配置和 Kubernetes 配置运行此检查；回显检查仅验证代理传输行为，不能替代上述真实后端认证验证。

该测试还会停止上游监听，确认 502 页面显示 modelOne、禁止缓存、Logo/favicon 仍可加载，并验证应用返回的 JSON 错误未被替换。使用 `--error-pages dist/modelone/frontend-errors` 检查部署生成的品牌页面；CI 会额外挂载带企业测试配置的页面执行同一故障检查。

应用测试加 `--https` 时需要本机 OpenSSL：使用 `STAGE=prod` 的真实 Gunicorn 进程、Secure cookie 和额外的隔离 TLS 网关，后端仅信任测试前端 IP。临时证书仅加入本次 Python 客户端的信任上下文，验证主机名与证书，并检查默认客户端拒绝该证书；不修改系统或浏览器证书库。测试验证 HTTPS 同源登录、跨站拒绝、直连后端伪造转发头被拒绝，以及网关覆盖客户端协议头。可与 `--nginx-config` 合用以检查 Kubernetes 前端配置。临时网络、证书和容器自动清理；该模式不连接正式证书、Ingress/Istio、企业 SSO 或真实集群，未纳入需要企业后端镜像的远程 CI。

报告为 `dist/modelone/mysql-validation.json`、`frontend-image-validation.json` 和 `app-smoke-validation.json`。通过后仍须对正式企业镜像、目标数据库和 Kubernetes 集群复测。
