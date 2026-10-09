# AIHub 模块

AIHub 有独立页面 `/aihub/` 和业务接口 `/aihub/api/`。源代码位于 `myapp/aihub/`，旧 `/model_market/*/api` 与 `Aihub` 表仅为兼容目录，不作为新页面数据源。页面不使用平台通用卡片路由或品牌配置；首期共享已有登录、用户、项目空间和数据库。

## 首期功能

- 已发布应用目录、分类与搜索、版本详情、端点健康状态。
- JSON Schema 驱动的文本/数字/布尔输入和同步在线体验。
- 管理员创建/编辑草稿、校验端点后发布、下架版本；发布后不可修改。
- 三种可见范围：平台、项目成员、创建者。目录、详情、健康检查和调用统一校验。
- 版本化推理 API 与调用审计，记录调用者、耗时和错误类型，不记录原始输入。

## 运行端点协议

端点地址由管理员登记。端点必须实现：

| 请求 | 响应 |
| --- | --- |
| `GET /metadata` | `{"application_id":"text-classifier","version":"1.0.0","revision":"sha256:..."}` |
| `GET /health` | `{"status":"ok"}` |
| `POST /predict`，请求 `{"inputs":{"text":"..."}}` | `{"result":{...}}`，结果符合登记的输出 JSON Schema |

发布和调用都会核对应用 ID、版本及修订。端点鉴权可通过服务端环境变量引用配置；客户端 Cookie 或 API 令牌不传给端点。首期仅支持同步 JSON 请求，文件、流式和异步能力尚未开放。

## 主要路由

| 路由 | 用途 |
| --- | --- |
| `GET /aihub/api/apps` | 可见应用目录，支持 `q`、`category`、`page` |
| `GET /aihub/api/apps/<slug>` | 详情与已发布版本 |
| `GET /aihub/api/apps/<slug>/versions/<version>/health` | 端点状态 |
| `POST /aihub/api/apps/<slug>/versions/<version>/predict` | 推理调用，使用平台会话或限时 API 令牌 |
| `/aihub/api/admin/apps` | 管理员草稿与版本管理 |

上线前运行数据库迁移 `myapp db upgrade`。完整产品范围和分期见[功能设计](../modelone/aihub-functional-design.md)。

管理员还需在平台配置中设置 `AIHUB_ENDPOINT_HOSTS` 为允许调用的推理主机名列表。默认空列表会拒绝登记运行端点；主机名需解析到实际推理服务，不接受回环或链路本地地址。通过环境变量保存的端点凭据只由后端进程读取。
