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

认证及 CSRF 行为沿用既有后端安全机制。不要把用户展示名称的变化当作接口路径变化。模型驱动接口的完整字段与实际响应需在部署环境导出，本说明不替代 OpenAPI 或接口回归报告。
