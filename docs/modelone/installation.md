# modelOne 安装部署手册

## 准备与构建

准备 Python 3.11（构建和检查工具）、Node.js 20、Docker Compose、kubectl、SQLAlchemy 和 PyYAML。运行容器仍使用其 Dockerfile 指定的 Python 版本。先填写 `config/modelone.json`；企业差异也可使用 `MODELONE_*` 环境变量覆盖。

```sh
python3 scripts/generate_brand.py
python3 scripts/test_modelone.py
for app in frontend vision visionPlus; do
  npm ci --prefix "myapp/$app" --legacy-peer-deps --no-audit --no-fund
  npm run build --prefix "myapp/$app"
done
python3 scripts/brand_scan.py --built
python3 scripts/resource_inventory.py
python3 scripts/compliance_inventory.py
python3 scripts/render_deployment.py --release
```

`--release` 要求企业仓库、版权方、帮助和支持配置，不等于完整发布验收。清单输出在 `dist/modelone`；未提供企业配置时可省略此参数生成开发预览。

镜像仓库配置格式为 `registry.example.com/team`，不要附加 `/modelone`。渲染器将工作负载镜像写为 `<仓库>/modelone/<镜像>:<标签>`。Compose 直接使用源文件时，`MODELONE_IMAGE_PREFIX` 必须包含尾随 `/`；后端的 `MODELONE_IMAGE_REGISTRY` 不包含尾随命名空间。环境变量覆盖通过渲染器写入容器；直接使用源 Compose 时以挂载的 JSON 配置为准。

## 镜像与资源

清单中的 `pending` 项尚未同步，不能用不存在的 `modelone/` 默认镜像启动生产。审核清单并登录仓库后，可运行 `python3 scripts/resource_inventory.py --copy-images`；需要安装 skopeo，它保留多架构镜像并比对摘要。资源可用 `--download-assets <暂存目录>` 下载，工具记录 SHA-256；上传企业存储或打入离线包后需逐项验证访问与校验和。盘点包含历史文档和示例引用，需要按企业保留清单筛选。

`assetBaseUrl` 应是浏览器和任务容器均可访问的完整 HTTP(S) 地址。默认 `/static/assets/modelone/` 只用于静态品牌和本地页面，不能直接当作容器中 wget/curl 的完整 URL。外部模型、教程和数据未打入本次代码改造，安装前必须准备好。

## Docker Compose

渲染文件中的挂载路径指向当前源码目录，不是可移机使用的独立安装包。先构建并推送企业后端和前端镜像。后端构建参数 `MODELONE_IMAGE_PREFIX` 当前作为前缀使用，传入时需包含尾随 `/`；基础镜像必须已同步。

```sh
docker compose -f dist/modelone/compose.yaml config --quiet
docker compose -f dist/modelone/compose.yaml up -d
```

启动前修改数据库和 Redis 凭据、确认持久化路径、配置 kubeconfig 并限制服务监听范围；源 Compose 的 admin 凭据仅为开发默认值。平台计算任务须连接 Kubernetes。

## Kubernetes

渲染器保留既有命名空间、服务名、选择器和 CRD，添加 modelone 应用标签和品牌 ConfigMap。企业环境需预建数据库、存储、控制器、镜像拉取 Secret 以及 kubeconfig；所需资源参照既有 install/kubernetes 基础设施目录。

```sh
kubectl apply --dry-run=server -f dist/modelone/kubernetes.yaml
kubectl apply -f dist/modelone/kubernetes.yaml
kubectl -n infra rollout status deployment/kubeflow-dashboard
```

正式域名和 TLS 证书需要在实际入口网关配置并验证。当前未配置目标集群，尚未执行上述集群命令。完全离线安装还需所有第三方镜像、软件包及模型文件的闭环验证。
