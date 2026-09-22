# modelOne API 说明

下表为源码已核实的 API 基址，保持原路径以兼容 SDK。字段、动作和访问权限由后端模型与视图决定；调用前在目标环境读取对应元数据并使用受控账号验证。

| 模块 | API 基址 |
| --- | --- |
| Notebook | `/notebook_modelview/api` |
| Notebook SDK | `/notebook_modelview/sdk` |
| Pipeline | `/pipeline_modelview/api` |
| 任务模板 | `/job_template_modelview/api` |
| 数据集 | `/dataset_modelview/api` |
| 推理服务 | `/inferenceservice_modelview/api` |
| 智能问答配置 | `/chat_modelview/api` |
| 智能会话 | `/aitalk_modelview/api` |
| AIHub 全部应用 | `/model_market/all/api` |
| 浏览器品牌配置 | `/myapp/brand.js`（公开、只读、无凭据） |
| 浏览器安装清单 | `/myapp/manifest/<app>.json`（公开、只读；app 为 `frontend`、`vision`、`visionPlus`） |

品牌配置与安装清单返回 `Cache-Control: no-store`；清单使用运行时产品名称、颜色和图标，并限定各应用的启动地址与作用范围。未识别的应用名返回 404。公开响应不包含镜像仓库、TLS Secret 等基础设施配置。

业务接口请求通过 `Authorization` 传递有效 API 令牌，支持两段短令牌、完整 JWT 或 `Bearer <JWT>`。从用户资料获取新令牌，默认 30 天过期；不接受原始用户名或旧固定密钥签发的凭据。停用账号的既有会话和令牌均被拒绝。

浏览器密码登录使用 `/login/` 的 CSRF 表单。保留 `/login/api/` 路径用于 POST JSON `{"token":"<有效API令牌>"}`，不接受 GET 或查询参数，不根据 `uuid` 等调用参数修改账号组织。请勿将令牌放进 URL、公开配置或日志。任务令牌不能用于建立会话；仅限数据集、项目、模型登记和推理接口，仍执行原有权限检查。

模型驱动接口的字段、写操作 CSRF/权限和实际响应需在目标环境逐项验证，本说明不替代 OpenAPI 或完整接口回归报告。
