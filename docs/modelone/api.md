# modelOne API 说明

下表为源码已核实的 API 基址，保持原路径以兼容 SDK。字段、动作和访问权限由后端模型与视图决定；调用前在目标环境读取对应元数据并使用受控账号验证。

| 模块 | API 基址 |
| --- | --- |
| Notebook | `/notebook_modelview/api` |
| Notebook SDK | `/notebook_modelview/sdk` |
| Pipeline | `/pipeline_modelview/api` |
| 首页 Pipeline | `/pipeline_modelview/home/api` |
| 任务模板 | `/job_template_modelview/api` |
| 模型登记 | `/training_model_modelview/api` |
| 模型管理页面 | `/training_model_modelview/web/api` |
| 数据集 | `/dataset_modelview/api` |
| 推理服务 | `/inferenceservice_modelview/api` |
| 智能问答配置 | `/chat_modelview/api` |
| 智能会话 | `/aitalk_modelview/api` |
| AIHub 全部应用 | `/model_market/all/api` |
| AIHub 分类 | `/model_market/{visual,voice,language,multimodal,aigc}/api` |
| ETL 编排 | `/etl_pipeline_modelview/api` |
| AutoML | `/nni_modelview/api` |
| 浏览器品牌配置 | `/myapp/brand.js`（公开、只读、无凭据） |
| 浏览器安装清单 | `/myapp/manifest/<app>.json`（公开、只读；app 为 `frontend`、`vision`、`visionPlus`） |

品牌配置与安装清单返回 `Cache-Control: no-store`；清单使用运行时产品名称、颜色和图标，并限定各应用的启动地址与作用范围。未识别的应用名返回 404。公开响应不包含镜像仓库、TLS Secret 等基础设施配置。

模型驱动页面使用 `GET <基址>/_info` 获取字段、标题、权限和表单配置；响应直接包含 `route_base`、`primary_key`、`list_columns` 和 `label_columns`。通用项目选择器 `/project_modelview/api` 没有页面标题，项目管理页使用 `/project_modelview/org/api`。

列表使用 `GET <基址>/?form_data=<JSON>`，分页参数为 `{"page":0,"page_size":20,"str_related":1}`。成功响应包含 `status: 0`、`result.count` 和 `result.data`，需同时检查 HTTP 状态和业务状态。模型、数据集和推理列表可能把历史版本放入 `children`，校验记录总数时需一并计算。首页 `/pipeline_modelview/api/my/list/` 和 `/pipeline_modelview/api/demo/list/` 的 `result` 直接是数组。

隔离容器测试已使用密码登录后的会话读取 20 组列表及元数据，检查全部分页、初始化记录和运行时品牌，并读取 6 个导航/快捷列表。测试不点击响应中的动作链接，不启动 Notebook、训练或推理，也不验证外部图片和模型文件可用性。请求方法为 GET 不代表无副作用，例如部分部署和重置操作同样使用 GET，调用前须核对具体路由。

业务接口请求通过 `Authorization` 传递有效 API 令牌，支持两段短令牌、完整 JWT 或 `Bearer <JWT>`。从用户资料获取新令牌，默认 30 天过期；不接受原始用户名或旧固定密钥签发的凭据。停用账号的既有会话和令牌均被拒绝。

浏览器密码登录使用 `/login/` 的 CSRF 表单。保留 `/login/api/` 路径用于 POST JSON `{"token":"<有效API令牌>"}`，不接受 GET 或查询参数，不根据 `uuid` 等调用参数修改账号组织。请勿将令牌放进 URL、公开配置或日志。任务令牌不能用于建立会话；仅限数据集、项目、模型登记和推理接口，仍执行原有权限检查。

模型驱动接口的字段、写操作 CSRF/权限和实际响应需在目标环境逐项验证，本说明不替代 OpenAPI 或完整接口回归报告。
