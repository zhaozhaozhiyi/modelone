# modelOne 开发基线验收记录

日期：2026-09-22。分支：`codex/modelone-brand-baseline`。本记录区分本地代码检查与真实环境验收；总体目标尚未完成。

| 验收标准 | 当前证据 | 剩余验收 |
| --- | --- | --- |
| 1. 所有用户页面显示 modelOne | 主门户、独立登录页、两个编排器、服务端页面已改造，三个前端生产构建通过 | 使用正式 Logo，在真实登录会话中逐页检查 |
| 2. 无旧名称、Logo、仓库、社区、Wiki | 产品源码、编译包、modelOne 交付文档、任务模板和镜像生成器扫描通过，旧 Logo 文件和回退路径已删除 | 实际浏览器网络与页面检查；视频、图片中的嵌入内容审核 |
| 3. 无原开源版/商业版说明 | 文案扫描通过 | 历史数据库与运行时接口响应检查 |
| 4. 标题、favicon、PWA、错误页 | 三个前端入口、清单和图标已通过真实 Nginx HTTP 检查；运行时安装清单通过后端容器 HTTP 验证，实际构建页面通过 JSDOM 脚本验证；CI 也会重建并检查前端交付镜像；独立登录模板、错误页和品牌脚本均读取统一配置 | 正式配置、浏览器安装体验、认证失败和服务异常页面实测 |
| 5. 不依赖原资源与镜像仓库 | 引用解析和迁移清单已实现；147 个镜像、943 个资源待筛选；门禁须当次验证企业目标摘要/校验和，仅下载不算完成 | 实际同步、镜像摘要与资源 SHA-256 比对、容器及浏览器网络检查 |
| 6. 初始化及历史数据品牌 | SQLite 与隔离 MySQL 8.0.46 迁移覆盖展示字段、链接、预览资源、JSON、空值与幂等 | 对企业全量 MySQL 备份副本进行迁移、核对及回退演练 |
| 7. Notebook 等业务正常 | 构建和迁移层检查通过；Notebook 九项测试中八项通过，覆盖无 SSH 凭据、真实公钥解析和 Spark 幂等，容器启动失败传播测试因未提供验证镜像而条件跳过 | Notebook、Pipeline、训练、模型、推理、AIHub 端到端回归 |
| 8. Docker/Kubernetes 部署 | Compose/Kustomize 渲染、前后端验证镜像构建、隔离后端启动及本地账号认证通过；认证、数据库和 Redis 私密注入检查通过；两个集群启动入口现在只接受已渲染的 modelOne 发布清单，并把所有源码 `-f/-k` 引用映射到镜像重写树，同时注入 `MODELONE_SERVICE_EXTERNAL_IP`；发布清单重写器已支持企业域名和 TLS Secret，CI 用隔离域名验证 Gateway、VirtualService 和四个 Ingress 的域名/TLS 生成；Ingress 已升级为 `networking.k8s.io/v1`，并清理已移除的 HPA/RBAC API；CI 在前端交付镜像上执行真实离线保存/导入校验 | 企业镜像构建、基础设施生产配置、全量依赖部署、正式域名/TLS 证书、企业认证与存储验证 |
| 9. 新安装及升级 | 隔离空库初始化通过；重复管理员初始化保留密码；MySQL 样本迁移与备份恢复记录一致，拒绝损坏备份和非空目标 | 企业全量已有环境升级、旧令牌与任务凭据迁移、持久卷恢复与离线演练 |
| 10. 生产无 source map | 本地产物和 legacy `appbuilder` 静态目录扫描通过；Docker/Kubernetes Nginx 配置加入拒绝规则，容器实测 map 请求为 404；CI 会执行同一前端镜像 HTTP 门禁 | 对最终企业镜像、集群入口和发布服务器再次检查 |
| 11. 自动阻止旧品牌回归 | 扫描器回归通过；CI 包含源码、安装文档、构建产物、任务模板和镜像生成器门禁 | 自有仓库运行 CI 并将检查设为合并/发布必需项 |
| 12. 许可证与版权 | 原 LICENSE 保持不变，生成 4,675 条已安装依赖声明、CycloneDX 1.5 前端 SBOM 和 LICENSE/NOTICE 证据清单 | 1,619 条依赖记录待人工复核；最终 Python/系统/镜像 SBOM 与许可证归档 |

本地品牌/发布回归三十四项、认证回归七项通过。2026-09-22 新增 Notebook 九项（八项通过、一项因未提供验证镜像而条件跳过）、节点部署五项、资源门禁十项、镜像包十一项和发布清单映射十项验证：Notebook 容器检查挂载当前启动脚本；节点测试替代 SSH/Docker，不连接真实节点；资源测试使用本地 HTTP 服务验证下载不足以发布、目标缺失、内容变化、断点校验以及旧 OSS/Tencent Cloud 主机和重定向拒绝；镜像包测试在本地缓存镜像和 CI 前端交付镜像上验证企业目标映射、归档校验、真实保存/导入、完整导入前检查、部署清单重写和批量重写 CLI（未提供缓存镜像时真实保存/导入用例才会条件跳过）；清单映射测试验证源码相对路径、`kubectl -f/-k` 重写、缺失清单、路径穿越拒绝、Ingress 域名/TLS 和已移除 Kubernetes API；新增独立 modelOne 登录模板、PWA 清单配置、`configure_modelone_remotes.py` 及回归测试，确保企业 `origin` 由参数显式设置、原仓库 `upstream` 禁止推送；镜像计划生成器可读取统一品牌配置，正式 Compose 产物改为企业镜像、命名数据卷和显式 kubeconfig 挂载。任务模板、三个前端 `public` 源目录、统一品牌配置、遗留主题模板和品牌静态资源均纳入扫描门禁；legacy `appbuilder` 静态资源移除了 source-map 引用，并删除了失效的 YOLOv8 旧安装钩子。发布 CI 现在生成 1,090 条资源盘点记录和前端依赖许可证证据清单，并校验两类报告结构；这一步不把 `pending` 或 `reviewRequired` 记录误判为已完成迁移或法律审计。

MySQL、前端镜像和应用容器验证已通过；本次使用当前 Dockerfile 从缓存基础镜像重建 `modelone/validation-backend:20260922`，实际 HTTP 已验证 modelOne 独立登录模板、密码登录、CSRF、拒绝用户名/Host 绕过、令牌签名与有效期、任务用途限制、账号停用、退出及重复管理员初始化。报告保存在 `dist/modelone/app-smoke-validation-20260922/app-smoke-validation.json`，密钥渲染检查为 `deployment-auth-validation.json`。该验证不代表企业正式镜像、Notebook 镜像或生产集群已经验收。

前端构建仍有既有 lint、依赖和包体积告警，Kustomize 有旧配置语法提示。应用初始化记录到已捕获的 `nickname` 列重复提示，需在企业升级演练核对。集群启动脚本（`start.sh`、`start-with-kubesphere.sh`）拒绝直接应用源码 Argo 清单和 Kustomize overlay，必须先提供经过镜像计划重写和品牌扫描的 `dist/modelone` 发布清单及完整 `platform-manifests/kubernetes` 清单树；节点地址通过受控环境变量注入，不再原地修改源码配置。认证绕过已在本地修复；[安全检查](security-review.md)中的企业认证、基础设施生产配置、旧凭据迁移及目标环境检查仍未验收。

下一步输入：企业 Git 与镜像仓库、对象存储/CDN、企业名称及品牌资产、帮助/支持/协议/隐私地址、正式域名与 TLS、登录方式、目标环境和数据库备份、离线要求及保留资源清单。凭据使用本机已登录会话或受保护配置提供。

原仓库为只读 `upstream`；企业仓库尚未提供，因此未设置 `origin`，也未创建正式发布标签。本地镜像构建使用已缓存的上游基础镜像验证改造代码，未执行远程推送、企业镜像复制、生产数据库修改或集群部署。

补充清单验证：修复 generator 配置文件漏带后，主平台（13 个资源、2 个镜像）和训练控制器（11 个资源、1 个镜像）已从发布清单树通过实际 Kustomize 构建，镜像全部匹配企业计划，编译结果通过品牌扫描。新增测试会移除原始目录后再构建，另覆盖文件缺失、目录越界、重叠输出和镜像参数重复改写。此验证不连接 Kubernetes API Server，不代表集群部署通过。

入口验证补充：四个可选 Ingress 的路径不再冲突，Service 名称和端口已与对应部署清单逐项核对。新构建的 `modelone/validation-frontend:20260922-routing` 在隔离容器中分别使用 Docker 默认配置和 Kubernetes Nginx ConfigMap，通过相对首页重定向、三个品牌入口、PWA/图标、source map 拒绝及许可证校验；报告为 `dist/modelone/routing-validation-20260922/docker-frontend.json` 和 `kubernetes-frontend.json`。同一镜像完成真实离线保存、导入和损坏归档拒绝，镜像包十一项全部通过。本次没有运行真实 Ingress 控制器或 TLS 证书握手，仍须在目标集群核验路由与证书。

运行时品牌验证补充：三个前端重新生产构建，JSDOM 执行实际页面的默认脚本与后端生成脚本，验证静态回退、标题、颜色、自定义 PNG 图标、各入口安装清单切换与重复加载。新构建的 `modelone/validation-backend:20260922-runtime-brand` 在隔离 MySQL/Redis 环境完成空库初始化和认证回归，三个公开安装清单通过部署环境变量覆盖、应用范围、响应类型及禁缓存检查，未知应用返回 404。对应前端镜像通过三个入口、PWA/图标、编译资源、相对重定向、source map 拒绝和原许可证 HTTP/文件检查。报告保存在 `dist/modelone/runtime-brand-validation-20260922/app/app-smoke-validation.json` 和 `frontend.json`；品牌扫描通过。JSDOM 检查不覆盖浏览器实际安装界面及已安装应用的更新行为，容器验证不覆盖生产集群、企业 SSO 或业务任务。

前后端入口联测补充：旧前端镜像经代理执行外站令牌登录时返回 200，复现了 `Origin` 被清空导致后端来源检查失效的问题。修复后构建 `modelone/validation-frontend:20260922-proxy`，Docker 默认配置及挂载的 Kubernetes 配置均通过真实后端联测：三个产品入口、运行时品牌和 PWA、密码与令牌认证、同源登录成功、外站及 `null` 来源返回 401 且不建立会话、401/404 品牌页面及退出行为。报告为 `dist/modelone/proxy-validation-20260922/docker-app/app-smoke-validation.json` 和 `kubernetes-app/app-smoke-validation.json`；修复前报告保存在同目录的 `before/`。两套配置的前端镜像检查也通过请求头透传、静态资源、source map 拒绝和许可证校验，报告为 `docker-frontend.json`、`kubernetes-frontend.json`；请求头回归已由现有 CI 步骤执行。此联测使用本地开发后端和 HTTP，未覆盖生产 Gunicorn 代理信任配置、TLS 握手、浏览器实际操作、WebSocket 完整连接或集群业务任务。

代理故障页面验证补充：修复前镜像在上游停止监听后返回默认错误页；新镜像 `modelone/validation-frontend:20260922-errors` 在 Docker 和 Kubernetes 配置下均返回 modelOne 页面，保留 502、设置 `Cache-Control: no-store`，默认 Logo/favicon 在上游不可用时仍能加载，应用自身的 503 JSON 响应保持完整。部署配置生成的错误页目录挂载后与实际响应逐字比对通过；同一内容随 Kubernetes ConfigMap 输出，Compose 使用可随交付目录移动的只读挂载。三十四项品牌/发布回归通过，覆盖四种错误页的配置转义与两种部署挂载。报告位于 `dist/modelone/error-page-validation-20260922/`：`before.json`、`docker.json`、`kubernetes.json` 和 `deployment-errors.json`。浏览器中检查了桌面、390px 窄屏及键盘焦点；页面沿用现有品牌字体、颜色和恢复入口，按 Open Design professional 的层级与可访问性规则复核。真实故障注入覆盖连接拒绝产生的 502；500/503/504 的生成和映射已检查，未进行生产网关超时及集群故障演练。

HTTPS 生产启动验证补充：从当前源码构建 `modelone/validation-backend:20260922-tls`，与前端镜像 `modelone/validation-frontend:20260922-errors`、隔离 MySQL/Redis 和临时 TLS 网关配合。使用 `STAGE=prod`，实际检查 Gunicorn 为主进程，后端只信任固定测试前端 IP；证书校验开启，未配置临时信任的客户端拒绝连接。Docker 与 Kubernetes 前端配置均通过完整认证回归、HTTPS 同源跳转、Secure/HttpOnly/SameSite cookie、跨站及 null 来源拒绝、直连后端伪造协议头拒绝和网关覆盖客户端协议头检查。报告位于 `dist/modelone/tls-validation-20260922/docker/app-smoke-validation.json`、`kubernetes/app-smoke-validation.json`，包含镜像摘要和测试范围。证书仅在测试客户端内信任，容器/网络/私钥自动清理；未连接真实 Kubernetes API、Ingress/Istio、企业证书或 SSO，未执行业务作业和浏览器会话验收。
