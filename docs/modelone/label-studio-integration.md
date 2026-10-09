# Label Studio 集成

项目已固定集成 [Label Studio 1.23.2](https://github.com/HumanSignal/label-studio/tree/1.23.2)，源码许可证为 Apache-2.0。源码拉取到 `external/label-studio`，版本锁定在 `integrations/label-studio/upstream.json`；该目录不打进 modelOne 镜像，Label Studio 作为独立服务运行。

## Docker Compose

先生成私有配置，命令不会输出密码，也不会覆盖已有文件：

```sh
python3 scripts/init_label_studio.py \
  --output .modelone-secrets/label-studio.env \
  --host https://ai.example.com/labelstudio \
  --email admin@example.com
```

再把基础 Compose 渲染为单独文件：

```sh
python3 scripts/render_label_studio.py \
  --compose-base dist/modelone/compose.yaml \
  --output dist/modelone/compose-label-studio.yaml
docker compose --env-file .modelone-secrets/label-studio.env \
  --env-file .modelone-secrets/compose.env \
  -f dist/modelone/compose-label-studio.yaml up -d
```

Label Studio 只通过 modelOne 前端暴露在 `/labelstudio/`，并由 modelOne 登录会话保护。已登录的平台用户进入标注页面时，网关会传递短时签名身份，Label Studio 自动创建对应的非管理员账号，无需再次输入密码。浏览器不能直接提供这个身份头。现阶段这些账号加入同一个 Label Studio 组织；项目权限按该组织的社区版权限执行。

嵌入页面通过 `integrations/label-studio/compact.css` 和 `locale-zh.js` 精简并中文化界面：使用紧凑的 14px 管理后台字号，保留项目创建和项目列表，收起欢迎内容、成员邀请、推广提示及资源链接；Community 版的 Enterprise 徽标、企业模板、升级提示和企业专属说明会被隐藏。项目页仍保留面包屑、任务管理、导入导出和标注编辑入口。翻译层只处理已知产品界面文案，不修改用户的项目名称和标注内容。资源由前端网关注入，文件设置为不缓存；更新后重载前端 Nginx 即可生效。

公开地址 `LABEL_STUDIO_HOST` 必须与浏览器实际访问的域名、端口和 `/labelstudio` 路径一致，否则 Label Studio 生成的 CSS/JS 绝对地址可能没有平台登录 Cookie，页面会失去样式。首次生成的私有配置包含独立的 `LABEL_STUDIO_SSO_SECRET`；已有配置升级时也需新增该密钥，并在平台和标注服务中使用相同的值。切勿将此密钥放入前端页面。

## Kubernetes

生成两个命名空间使用的 Secret（输出文件权限为 0600），再渲染独立清单：

```sh
python3 scripts/init_label_studio.py \
  --output .modelone-secrets/label-studio-secret.json \
  --host https://ai.example.com/labelstudio \
  --email admin@example.com --kubernetes
python3 scripts/render_label_studio.py \
  --kubernetes-base dist/modelone/kubernetes.yaml \
  --cluster-dns 10.96.0.10 \
  --output dist/modelone/kubernetes-label-studio.yaml
kubectl apply -f .modelone-secrets/label-studio-secret.json
kubectl apply -f dist/modelone/kubernetes-label-studio.yaml
```

`--cluster-dns` 必须填写目标集群的真实 DNS Service 地址，不能使用示例值。生产环境应把镜像复制到企业镜像仓库，并通过 `MODELONE_LABEL_STUDIO_IMAGE` 或清单修改为企业镜像地址。

## 平台 API

平台侧 API 使用当前登录用户的 modelOne 会话，并要求请求携带用户自己的 Label Studio 令牌：

- `GET /label_studio/api/status`：检查服务状态
- `GET /label_studio/api/projects?page=1&page_size=20`：查询项目
- `POST /label_studio/api/projects`：创建项目
- `POST /label_studio/api/projects/{id}/import`：批量导入 1–1000 条任务
- `GET /label_studio/api/projects/{id}/export?all_tasks=true`：导出 JSON 标注

请求头格式为 `X-Label-Studio-Authorization: Token <个人令牌>` 或 `Bearer <JWT>`。平台不会保存令牌；单次导入限制 10 MiB，导出响应限制 64 MiB，较大数据集应使用 Label Studio 的存储同步或分批任务。

## 自动标注

现有 YOLOv8 Label Studio ML Backend 可继续使用。推理服务只需实现 Label Studio ML Backend 协议，模型预测结果由标注平台显示为预标注，人工确认后再通过导出接口或 Pipeline 转成训练格式。

## 关闭和升级

基础部署默认关闭标注入口。要关闭已启用的 Compose 集成，停止 `label-studio` 和 `label-studio-db` 服务即可；数据卷不要删除。升级时只修改 `upstream.json` 的 tag、commit 和镜像，并重新执行导入导出回归检查。
