# 训练流水线编排器与 ETL 编排器技术分析报告

> 分析日期：2026-10-10
>
> 代码版本：`codex/modelone-space-p0`，`84d83ce`
>
> 分析对象：`myapp/vision`、`myapp/visionPlus` 及其直接关联的模型、视图和初始化数据
>
> 报告性质：源码静态分析 + 无网络、无数据库的隔离执行验证；未修改编排器业务代码

## 1. 执行摘要

仓库中存在两套外观和交互高度相似、但业务模型明显不同的编排器：

- `myapp/vision` 是训练/机器学习流水线编排器。画布节点对应数据库中的真实 `Task`，Pipeline 负责保存拓扑和画布布局，最终生成 Argo Workflow 并提交 Kubernetes CRD。
- `myapp/visionPlus` 是 ETL 编排器。节点主要存在于前端快照和 `ETL_Pipeline.dag_json` 中，保存时整图提交，后端再同步 `ETL_Task`。调度引擎通过 Airflow、Azkaban、DolphinScheduler 适配类选择。

两套前端显然来自同一代码基线：53 个相同相对路径中有 25 个文件字节级完全一致，共享 React Flow 画布、Redux slice、设置面板和 Monaco 编辑器等结构。但它们不能简单合并成一套业务实现，因为节点身份、保存事务和运行后端完全不同。更合理的方向是共享画布与表单基础设施，在上层保留 `TrainingAdapter` 和 `EtlAdapter` 两套领域适配器。

当前最需要先处理的不是界面重构，而是数据一致性：

1. 训练编排器后端的环检测条件恒为假，循环依赖或未知上游会被静默截断成部分/空 DAG。
2. ETL 仅编辑画布而未打开全局设置时，会把已有全局 `config` 保存成空对象。
3. 两套编排器点击“运行/提交”后都没有等待 Pipeline 保存完成，可能执行旧版本拓扑。
4. 训练 Task 保存失败后仍清空待保存修改；ETL 在 HTTP 完成前显示已保存，业务错误也会清除编辑态。
5. ETL 的三个调度适配器目前仍是占位实现，只返回硬编码外部地址，没有真正创建、更新或删除远端工作流。

综合判断：训练编排器已经形成了真实的 Argo 执行链，但保存和校验可靠性不足；ETL 编排器目前更接近“可视化配置编辑器 + 调度适配器骨架”，不应按完整调度集成来评估或承诺。

## 2. 范围、方法与限制

### 2.1 分析范围

本次覆盖：

- 两套前端的入口、路由、组件树、Redux 状态、模板加载、节点表单、保存和运行逻辑；
- 训练侧 `Pipeline` / `Task` 模型、Pipeline API、Argo Workflow 生成和 Kubernetes 提交；
- ETL 侧 `ETL_Pipeline` / `ETL_Task` 模型、自定义配置 API、任务同步和三种调度器适配类；
- `init-job-template.json`、`init-etl-pipeline.json` 中的初始化数据；
- 构建配置、依赖、测试目录和部署输出路径。

不在本次范围：真实浏览器交互、数据库迁移执行、登录/权限集成测试、Kubernetes/Argo 实际提交、外部调度器连通性及性能压测。

### 2.2 方法

- 逐文件静态阅读关键调用链；
- 对入口、相对路径和字节完全相同文件做规模统计；
- 用仓库已有 TypeScript 编译器转译实际 Redux thunk，并注入内存 API mock 执行失败和延迟场景；
- 从 `view_pipeline.py` AST 中提取实际 `order_by_upstream` 函数，隔离执行合法 DAG、循环 DAG 和未知上游 DAG；
- 不启动真实服务、不写数据库、不访问集群。

### 2.3 源码规模

| 指标 | 训练编排器 `vision` | ETL 编排器 `visionPlus` |
|---|---:|---:|
| `src` 下全部文件 | 60 | 53 |
| TS/TSX/JS/JSX/CSS/Less 等代码行 | 5,642 | 4,398 |
| 两侧共同相对路径 | 53 | 53 |
| 共同路径中字节完全相同 | 25 | 25 |
| 完全相同文件行数 | 898 | 898 |

上述数字说明复制关系很强，但“同名文件”并不等于“相同语义”；保存模型正是两者最核心的分歧点。

## 3. 总体能力对比

| 维度 | 训练编排器 | ETL 编排器 |
|---|---|---|
| 前端目录 | `myapp/vision` | `myapp/visionPlus` |
| 面向场景 | 训练、数据处理、模型评估、部署 | 通用 ETL / 外部调度配置 |
| 页面参数 | `pipeline_id` | `pipeline_id` + `scenes` |
| 实际 `scenes` | 不使用 | `etl_pipeline` |
| 模板来源 | `/job_template_modelview/api/` | `/{scenes}_modelview/api/template/list/{id}` |
| 初始化模板 | 96 个，其中 94 Release、2 Alpha | 1 条示例 Pipeline；模板由引擎适配类返回 |
| 节点主键 | 数据库 `Task.id` 的字符串形式 | `${templateName}-${timestamp}` |
| 新增节点 | 先 POST 创建 Task，再放入画布 | 只在前端创建本地节点 |
| 节点配置持久化 | 每个 Task 单独 PUT | 随整张 DAG 快照 POST |
| Pipeline 持久化 | PUT Pipeline：变更字段 + `expand` | POST 全量配置：`dag_json` + `config` |
| DAG key | Task 名称 | 前端节点名称/ID |
| 运行后端 | Argo Workflow + Kubernetes CRD | 按 `workflow` 动态加载调度适配器 |
| 当前调度成熟度 | 已有真实 K8s 提交链 | 适配器仍是占位跳转实现 |
| 前端路由 | `/`、`/home` | `/` |

## 4. 共同前端架构

### 4.1 技术栈

两侧均使用：

- React 17；
- Redux Toolkit 1.5 + React Redux 7；
- React Router 5，`HashRouter`；
- React Flow Renderer 9.4；
- Fluent UI 8 和 Ant Design 4.17.4；
- Monaco Editor；
- Axios 0.21；
- TypeScript 4.5。

包名虽然是 `vite-ml-platform`，实际并未使用 Vite，而是 Create React App + `react-app-rewired` + Webpack。两个 `build` 脚本都设置了 `TSC_COMPILE_ON_ERROR=true`，意味着 TypeScript 错误不会阻止生产构建，降低了类型检查作为发布门禁的价值。

生产构建目录保留了历史拼写：

- 训练：`myapp/static/appbuilder/vison`；
- ETL：`myapp/static/appbuilder/visonPlus`。

这些路径已被后端跳转依赖，修正 `vison` 拼写需要兼容迁移，不能直接改名。

### 4.2 页面组件树

两侧主页面基本一致：

```text
Provider + HashRouter
└── Index
    ├── ModuleTree        模板库、搜索、拖拽源
    ├── FlowEditor
    │   ├── EditorHead    标题、设置、运行/提交
    │   ├── EditorTool    保存、删除、日志/跳转等工具
    │   └── EditorBody    React Flow 画布
    │       └── DataSet   自定义节点及节点配置 Model
    └── EditorAce         全局 Monaco 编辑器浮层
```

画布使用统一的 `dataSet` 节点类型，顶部为 target handle，底部为 source handle；包含 MiniMap、Controls 和 `[16, 16]` 网格吸附。

### 4.3 Redux 状态

两侧 store 都包含：

| slice | 职责 |
|---|---|
| `app` | 用户和错误提示 |
| `editor` | Monaco 显示、当前 key/value/type |
| `element` | React Flow nodes/edges、选中项 |
| `pipeline` | 当前 Pipeline、dirty/saved/editing 状态 |
| `setting` | 全局设置面板显示状态 |
| `task` | 节点参数变更 Map、当前 taskId |
| `template` | 模板面板状态 |

store 调用了 `enableMapSet()`，并关闭 Redux Toolkit 的 `serializableCheck`。这样可以把 `Map` 和部分 UI 对象直接放进 store，但也失去了不可序列化状态警告、时间旅行调试和可靠持久化的基础。

### 4.4 共性工程缺口

- 两套目录都没有发现应用级 `*.test.*` / `*.spec.*`；
- 两侧本地 `node_modules` 都不存在，当前环境不能直接运行各自 `react-app-rewired test/build`；
- 未看到 `beforeunload` 未保存保护、undo/redo、图版本号或乐观锁；
- 未看到 `isValidConnection` 或前端环检测；
- 未看到 WebSocket、SSE 或轮询驱动的节点运行状态更新；
- DAG 生成对每条 edge 都重新扫描全部 elements，复杂度约为 `O(E × (V + E))`；
- 每个自定义节点都挂载自己的 Model 组件，并订阅全局编辑器状态，大图下会扩大无效渲染成本。

## 5. 训练流水线编排器

### 5.1 初始化与模板库

`ModuleTree` 请求 `/job_template_modelview/api/`，显式指定所需字段；前端只保留 `version === "Release"` 的模板，并按模板所属 project 分组。模板结果缓存在 localStorage 的 `job_template` 中，有效期 24 小时。

当前 `init-job-template.json` 是对象而不是数组，共 96 个模板：没有显式版本的模板按 CLI 默认值 `Release` 导入，另有 2 个显式 `Alpha`（`one-hot`、`pca`），因此初始化后的标准环境应有 94 个可见 Release 模板。实际部署数量仍以数据库接口为准。

关键代码：

- 模板查询：[myapp/vision/src/api/index.ts](../../myapp/vision/src/api/index.ts#L5)
- Release 过滤和分组：[myapp/vision/src/components/ModuleTree/index.tsx](../../myapp/vision/src/components/ModuleTree/index.tsx#L52)
- 24 小时缓存：[myapp/vision/src/components/ModuleTree/index.tsx](../../myapp/vision/src/components/ModuleTree/index.tsx#L86)
- 初始化导入默认版本：[myapp/cli.py](../../myapp/cli.py#L128)

### 5.2 新增节点：远端实体优先

用户把模板拖入画布时，前端不是先创建临时节点，而是：

1. 从模板参数 schema 收集默认值；
2. POST `/task_modelview/api/` 创建真实 Task；
3. 默认挂载 workspace PVC 到 `/mnt`，设置 2G 内存、2 CPU、0 GPU 和 `cpu=true,train=true`；
4. 用返回的数据库 Task ID 作为 React Flow node ID；
5. 更新画布；
6. 两秒后触发一次 Pipeline 保存。

代码位置：[myapp/vision/src/components/FlowEditor/components/EditorBody/index.tsx](../../myapp/vision/src/components/FlowEditor/components/EditorBody/index.tsx#L77)。

这个设计的优点是节点始终能关联真实 Task，单节点 debug/run/日志天然有稳定 ID。代价是拖拽动作依赖网络成功，而且 Task 创建和 Pipeline 画布保存不是一个事务；浏览器中途关闭或后一次保存失败时，可能留下数据库 Task 与画布快照不一致。

### 5.3 节点配置

选中节点后，Model 面板按 Task ID 请求详情，把模板默认参数与 Task 已保存的 `args` 合并。修改值后进入 `task.taskList: Map<taskId, changed>`，节点 label 同步回画布。

表单支持字符串、多行文本、choices、布尔、列表、JSON、Markdown tip、资源、跳过、debug/run/clear 等。必填标记主要用于显示，未形成“整图保存前统一校验”的门禁。

当前 96 个初始化模板的参数类型只有 `str`、`text`、`json`、`enum`，因此源码中的 `float` / `int` 控件问题属于扩展 schema 的潜在兼容问题，而不是当前初始化模板的立即回归：`SpinButton` 把整个 range 数组传给 `min/max`，递增/递减又固定为 1；float schema 缺少 range 时会访问 `undefined[0]`。

### 5.4 DAG 和画布持久化

前端从 edge 推导：

```json
{
  "downstream-task-name": {
    "upstream": ["upstream-task-name"]
  }
}
```

DAG 使用 Task 名称，不使用数据库 ID。只根据边生成时，孤立节点和根节点可能缺席；后端 `fix_dag_json` 和保存校验会补全没有上游的 Task。

Pipeline 保存包含：

- `pipeline.changed` 中的全局字段和 `dag_json`；
- `expand: JSON.stringify(elements)`，保存节点位置、边和展示信息。

Task 保存和 Pipeline 保存是两条独立请求链：Task 通过多个 PUT 并行提交，Pipeline 通过单个 PUT 保存拓扑和布局，没有共同事务或 revision。

### 5.5 运行链路

```text
运行按钮
  -> 保存 dirty Tasks
  -> 发起 Pipeline 保存（当前未等待）
  -> GET /pipeline_modelview/api/run_pipeline/{id}
  -> 删除旧 Task 运行资源和绑定 Workflow
  -> dag_to_pipeline / make_workflow_yaml
  -> 创建 Argo Workflow CRD
  -> 跳转日志页
```

后端运行前校验创建者/管理员权限。随后会删除已有手工运行 Workflow 和每个 Task 的运行实例，再生成新 Workflow，因此“运行”具有破坏既有运行资源的语义，需要在 UI 上明确并保证新配置已经可靠保存。

`run_pipeline()` 捕获 Kubernetes 异常后只打印，仍返回 `crd_name`；上层随后写入 `pipeline_argo_id` 并提交数据库，可能形成“记录已提交、集群实际失败”的假状态。

相关代码：

- 前端运行：[myapp/vision/src/components/FlowEditor/components/EditorHead/index.tsx](../../myapp/vision/src/components/FlowEditor/components/EditorHead/index.tsx#L44)
- DAG 排序校验：[myapp/views/view_pipeline.py](../../myapp/views/view_pipeline.py#L778)
- K8s 提交：[myapp/views/view_pipeline.py](../../myapp/views/view_pipeline.py#L541)
- 运行前删除与提交：[myapp/views/view_pipeline.py](../../myapp/views/view_pipeline.py#L1098)

## 6. ETL 编排器

### 6.1 `scenes` 的真实含义

ETL 前端从 URL 读取 `pipeline_id` 和 `scenes`，再拼接：

```text
/{scenes}_modelview/api/template/list/{pipeline_id}
/{scenes}_modelview/api/config/{pipeline_id}
```

当前后端跳转固定生成：

```text
/static/appbuilder/visonPlus/index.html?scenes=etl_pipeline&&pipeline_id={id}
```

因此当前 `scenes` 是 API namespace `etl_pipeline`，不是 `airflow`、`azkaban` 或 `dolphinscheduler`。具体调度引擎由数据库字段 `ETL_Pipeline.workflow` 决定，后端再动态 import 对应适配器。

### 6.2 API 协议

ETL 前端只有三个领域 API：模板列表、配置 GET、配置 POST。配置响应直接把业务字段放在顶层，不使用训练 API 的 `result` 包装：

```json
{
  "id": 1,
  "name": "dau",
  "label": "DAU pipeline",
  "project": "project description",
  "pipeline_ui_config": {},
  "pipeline_jump_button": [],
  "pipeline_run_button": [],
  "dag_json": {},
  "config": {},
  "message": "success",
  "status": 0
}
```

模板响应包含历史拼写：

```json
{
  "templte_common_ui_config": {},
  "templte_list": {},
  "template_group_order": []
}
```

`templte_*` 已是前后端 wire protocol 的一部分，不能只在单侧“修正拼写”；应在引入版本化 DTO/兼容层后再迁移。

后端返回的 `project` 当前是 `pipeline.project.describe` 字符串，而 Setting 初始化按 `{id, name}` 对象读取。项目选择控件目前被注释，所以主要表现为内部状态不一致；如果恢复该控件，协议必须先统一。

### 6.3 模板和新增节点

ModuleTree 每次加载都会请求后端，虽然写入了 `ft_job_template*` localStorage 缓存，但读取缓存的路径已被注释。模板按服务端 `template_group_order` 排列，公共 schema 与模板 schema 合并后用于动态表单。

拖入模板时不创建后端 Task，而是生成本地节点：

```text
id = templateName + "-" + timestamp
data.info = template / template-group / color / UI schema
data.config = common schema + template schema
```

随后更新 elements 并立即触发整图保存。加载已有 Pipeline 时，前端从 `pipelineInfo.dag_json` 重建 node/edge；优先采用服务端当前模板 schema，保存快照中的 schema 作为兼容回退。

### 6.4 保存模型

ETL 的 `task.saveTaskList()` 没有任何 API 请求，只遍历 Map 打日志；真正保存全部发生在 `pipeline.savePipeline()`：

1. 从 elements 找出所有 node；
2. 从各 node schema 生成默认参数；
3. 用 `task.taskList` 覆盖已编辑参数，否则回退到源 `dag_json`；
4. 写入位置、label、颜色、模板、模板组、task-config 和两套 UI schema；
5. 用 edge 推导的 upstream 覆盖关系；
6. POST 整个 Pipeline 配置。

后端保存后调用 `fix_pipeline_task()`，把 DAG 快照同步为 `ETL_Task` 记录；数据库内部 `id` 与远端调度系统 `etl_task_id` 是不同概念。

这种整图快照模型适合本地草稿，但当前没有 revision / `If-Match`，两个浏览器或两个快速保存请求会以后完成者覆盖先完成者。

### 6.5 调度适配器现状

存在三套约 985 行的引擎适配文件：

- `view_etl_pipeline_airflow.py`；
- `view_etl_pipeline_azkaban.py`；
- `view_etl_pipeline_dolphinscheduler.py`。

它们主要复制了模板 schema 和按钮定义，构造器默认 host 分别硬编码为 `http://airflow.oa.com`、`http://azkaban.oa.com`、`http://dolphinscheduler.oa.com`。三个 `submit_pipeline()` 都只返回空 DAG 和一个 `/code?dag_id=...` 跳转地址，`delete_pipeline()` 都是 `pass`。

后端列表页也明确提示：“此部分仅提供任务流编排能力，管理员自行对接调度平台能力”。因此当前运行按钮的实质是保存后跳转，并没有在仓库内实现远端 DAG 发布、更新、触发、状态回传和删除。

## 7. 保存与运行时序

### 7.1 训练编排器

```text
节点编辑 -> taskList Map
画布编辑 -> elements + pipeline.changed.dag_json

顶部“运行”:
await Task PUT 集合
dispatch(Pipeline PUT)       <- thunk 不返回 Promise
window.open(run URL)         <- 立即发生，可能读取旧 Pipeline

工具栏“保存”:
dispatch(Task save thunk)    <- 未 await dispatch 返回的 Promise
dispatch(Pipeline PUT)       <- Task 与 Pipeline 可并发
```

### 7.2 ETL 编排器

```text
节点/设置编辑 -> taskList + elements + pipeline.changed

保存:
dispatch(saved=false)
POST config                 <- Promise 链未 return
dispatch(saved=true)        <- HTTP 尚未完成就执行

提交:
await no-op Task save
dispatch(config POST)       <- 未等待
window.open(submit URL)     <- 立即发生，可能提交旧配置
```

这两条时序是当前一致性问题的核心。只在按钮层补一个 `await` 不够，thunk 本身必须返回可 reject 的 Promise，并在业务 `status !== 0` 时 reject。

## 8. 风险清单

严重度定义：

- **S0**：可导致错误执行、静默数据丢失或核心流程不可相信，应阻断发布；
- **S1**：高概率误导用户、保存不一致、权限或运行状态风险，应进入最近修复批次；
- **S2**：兼容性、维护性、性能或受条件限制的安全风险；
- **S3**：体验和代码卫生问题。

| ID | 严重度 | 结论 | 状态 |
|---|---|---|---|
| R-01 | S0 | 训练后端 DAG 环/未知上游校验恒失效，并静默截断 DAG | 静态确认 + 隔离复现 |
| R-02 | S0 | ETL 普通画布保存会把已有全局 `config` 覆盖成 `{}` | 静态确认 + 隔离复现 |
| R-03 | S0 | 两套运行/提交都不等待 Pipeline 保存完成 | 静态确认 + thunk 返回值验证 |
| R-04 | S1 | 训练 Task 保存失败后仍清空全部 dirty Map | 静态确认 + 隔离复现 |
| R-05 | S1 | ETL 提前显示已保存，业务错误仍清编辑态，可产生并发覆盖 | 静态确认 + 隔离复现 |
| R-06 | S1 | ETL 删除节点时先保存旧图，再从前端删除 | 静态确认 |
| R-07 | S1 | ETL 用 truthy 判断恢复值，`false`、`0`、空串会被默认值替换 | 静态确认 |
| R-08 | S1 | ETL 全局 JSON 编辑器确认值未回写 Setting | 静态确认 |
| R-09 | S1 | ETL 后端只在 task-config 含 `crontab` 时更新已有节点 | 静态确认，内置模板通常不触发 |
| R-10 | S1 | 训练 K8s 创建异常被吞掉，数据库仍可能记录 CRD 名 | 静态确认 |
| R-11 | S1 | ETL 自定义 GET/submit 路由未看到对象级项目权限检查 | 静态确认，需集成验证 |
| R-12 | S2 | ETL 外部绝对跳转 URL 被再次拼接 `window.location.origin` | 静态确认 |
| R-13 | S2 | 动态数值控件与 schema 不兼容 | 静态确认，当前训练初始化模板未使用 |
| R-14 | S2 | 模板说明和 SVG 直接注入 HTML，安全依赖上游写权限与净化 | 静态确认，利用性待验证 |
| R-15 | S2 | 训练“新建流水线”硬编码 `project: 7` | 静态确认 |
| R-16 | S2 | 两侧无 revision、离开保护、撤销重做和运行态同步 | 静态确认 |

## 9. 关键问题详解

### R-01：训练 DAG 校验恒失效

代码：

```python
if list(dag_json.keys()).sort() != list(order_dag.keys()).sort():
```

Python 的 `list.sort()` 原地排序并返回 `None`，因此这里实际比较 `None != None`，永远是 `False`。循环节点或引用未知上游的节点在 100 次循环后退出，未进入 `order_dag` 的内容被静默丢弃。

隔离执行实际函数得到：

```text
cycle => {}
unknown_upstream => {}
valid => {'a': {}, 'b': {'upstream': ['a']}}
```

影响：用户保存的图可能变成空 DAG 或部分 DAG；后续 `fix_dag_json` 还可能把丢失的 Task 重新补成独立根节点，使依赖关系被静默改变。

建议：使用显式拓扑排序，维护 indegree 和邻接表；发现剩余节点时返回结构化 4xx，列出 cycle/unknown upstream；后端测试至少覆盖空图、单节点、菱形、重复边、自环、多节点环和未知上游。

### R-02：ETL 全局配置被清空

ETL 保存参数固定为：

```typescript
config: JSON.parse(pipelineChange.args || '{}')
```

它没有回退到 `initProject.config`。Setting 初始化只写本地 state，不会把初始 config 写进 `pipeline.changed.args`；只移动节点或改连线时，POST 会携带 `{}`，后端又在请求含 `config` 时无条件覆盖数据库。

隔离执行实际 thunk 时，源配置 `{retain: "must-stay"}` 被提交为 `{}`。

建议：把领域状态规范化为 `draft.config`，加载时完整初始化；保存时提交完整、已验证的 draft。最小补丁也应使用“changed 中存在 args 才解析，否则使用 initProject.config”，并测试 `false`、`0`、空串、null 和嵌套 JSON。

### R-03：保存完成前运行

训练和 ETL 的 `savePipeline()` 都没有 `return api...`；调用方即使 `await dispatch(savePipeline())` 也只会得到 `undefined`。当前调用方甚至直接 dispatch 后立刻 `window.open`。

影响：网络较慢、保存失败或并发保存时，运行接口读取数据库旧版本。训练侧还会先删除旧运行资源，错误配置的后果更大。

建议：

1. thunk 返回 Promise；
2. HTTP 错误和 `status !== 0` 都 reject；
3. `saveAll()` 串行完成 Task 保存和 Pipeline 保存；
4. 运行按钮只在 `await saveAll()` 成功后打开运行 URL；
5. 保存期间禁用重复点击，并用 request ID/revision 防止旧响应覆盖新状态。

### R-04：训练 Task 失败后丢 dirty 状态

`Promise.allSettled(queue)` 的结果没有检查，无论 rejected 还是业务非零状态，都会 `resetTaskList()`。隔离执行一个 rejected 请求后观察到：

```text
promiseStatus: rejected
dispatched: updateLoading -> updateLoading -> resetTaskList
pendingChangesReset: true
```

还存在更隐蔽的并发问题：保存开始后用户继续编辑同一个 Map，旧请求完成时全量 reset 会清掉保存期间产生的新修改。

建议：为每项 dirty 记录本地版本；只移除“该版本已经成功保存”的条目，失败项保留并明确显示；业务状态非零同样算失败。

### R-05：ETL 保存状态是假状态

ETL thunk 在发出请求后立即 `updateSaved(true)`，Promise `finally` 又设置一次；`.then()` 则在检查 `status` 之前先 `updateEditing(false)`。工具栏还在请求发出前直接 `message.success('保存成功')`。

隔离执行延迟 Promise 证明：HTTP 尚未完成时 action 已是 `saved=false -> saved=true`；模拟 `{status: -1}` 后仍触发 `editing=false`。

建议把状态改成明确状态机：`idle | dirty | saving | saved | error`，成功消息只能由已校验的成功响应触发。

### R-06：ETL 删除顺序错误

画布 Delete 事件和工具栏删除都先 `dispatch(savePipeline())`，再 `updateElements(removeElements(...))`。Redux state 在保存读取时仍包含被删除节点；删除后的新 state 没有自动再保存，刷新页面时节点可能复活。

建议先产生 `nextElements`，一次性更新 draft，再以同一份 `nextElements` 构建并保存快照；不要依赖 effect 之后补齐。

### R-07：ETL falsy 值被默认值覆盖

节点 Model 和全局 Setting 均使用：

```typescript
if (savedValue[key]) use(savedValue[key]); else use(defaultValue);
```

这会把合法的 `false`、数值 `0`、空字符串重置为默认值。初始化示例中已有字符串 `"0"`，暂不触发；只要 schema 改用真正 number/bool 就会出现错误。

建议使用 `Object.prototype.hasOwnProperty.call(savedValue, key)` 或 `savedValue[key] !== undefined`。

### R-08：ETL 全局 JSON 编辑器未形成闭环

Setting 可以向全局 EditorAce 写入 key/value 并打开编辑器，但虽然导入了 `selectShowEditor/selectKey/selectValue`，并没有订阅这些 selector，也没有像节点 Model 那样监听确认后的 value。JSON TextField 又是 disabled，所以确认后全局配置不会回写；在特定选择状态下，全局 value 还可能被最近挂载的节点 Model 消费。

建议给编辑器引入显式 owner/context，例如 `{scope: 'pipeline' | 'task', entityId, key}`，确认时由单一 reducer 更新对应 draft，避免多个挂载组件竞相监听全局 value。

### R-09：ETL 后端更新依赖 `crontab`

后端对已有节点仅在下面条件成立时合并请求：

```python
if task_config and 'crontab' in task_config:
    new_dag_json[task_name].update(req_data['dag_json'][task_name])
```

内置 common schema 通常包含 `crontab`，因此标准模板多半可更新；自定义模板缺少该字段时，位置、label、依赖和参数都会被忽略。`crontab` 不应承担“这是合法完整节点”的哨兵职责。

建议使用版本化 DTO 校验必需字段，再无条件替换前端负责的字段，同时保留后端负责的 `task_id/etl_task_id`。

### R-10：训练提交失败被吞掉

`run_pipeline()` 捕获创建 CRD 的所有异常，只 `print(e)`，然后返回预先计算的 `crd_name`。调用方把该名称写进 `pipeline_argo_id` 并 commit。

建议让异常向上冒泡，或返回明确 Result；只有 Kubernetes API 确认创建后才写运行 ID。提交失败时不能把 Pipeline 标记为已运行。

### R-11：ETL 对象级权限边界待验证

`pipeline_config` GET、模板 GET 和 submit 都直接按 URL ID 查询；POST config 只校验创建者/管理员。文件中定义了 `check_pipeline_perms`，但未应用，而且读取 `kwargs['pipeline_id']`，路由参数实际叫 `etl_pipeline_id`。

这不等于“接口完全无认证”：`MyappModelRestApi` / Flask-AppBuilder 的全局认证和路由权限仍可能生效。但源码中没有看到普通用户是否属于该 Pipeline project 的对象级检查。需要用两个普通用户、不同项目做 HTTP 集成测试后才能定性为越权漏洞。

### R-12：ETL 跳转 URL 拼接错误

适配器的 jump button 返回绝对 URL，例如 `http://airflow.oa.com/tree?...`；前端工具栏统一拼接 `${window.location.origin}${item.action_url}`，结果会类似：

```text
https://platform.examplehttp://airflow.oa.com/tree?dag_id=...
```

建议统一协议：后端只返回相对平台 URL，或前端用 `new URL(action_url, window.location.origin)` 正确处理相对/绝对两种情况，并配置允许的外部 host。

### R-14：HTML/SVG 信任边界

两侧多处使用 `dangerouslySetInnerHTML` 展示模板 `describe`、Markdown 渲染结果或后端按钮 `icon_svg`，未看到 DOMPurify 等前端净化。是否能利用取决于谁能写模板、后端是否已净化、CSP 和 cookie 属性，因此本报告不直接宣称存在可利用 XSS。

建议明确这些字段的信任级别；服务端存储前白名单净化，前端展示前再次净化，并为 SVG 使用受控图标 ID 而不是任意 SVG 字符串。

## 10. 后端和数据模型评价

### 10.1 训练模型

训练侧职责分离总体清楚：

- `Pipeline` 保存项目级配置、DAG、画布 `expand`、调度参数和运行信息；
- `Task` 保存模板引用、资源、命令、参数、重试和超时；
- `fix_dag_json()` / `fix_expand()` 负责修复历史数据；
- `dag_to_pipeline()` 把数据库模型编译为 Argo Workflow。

主要问题不是领域边界，而是多实体保存没有事务契约、前后端校验结果没有可靠传播、运行流程吞异常。

### 10.2 ETL 模型

ETL Pipeline 把整图 JSON 和全局 config 保存为 Text，扩展灵活，但 schema 演化、字段所有权和并发控制都依赖约定。`ETL_Task` 作为派生表同步，既有内部主键又有远端 ID；目前调度适配器未实现，远端 ID 生命周期也就没有闭环。

三套引擎文件高度复制，未来真正接入时容易出现 schema 漂移。应把公共模板 schema、公共按钮和公共验证抽出，适配器只保留：

- `validate(draft)`；
- `publish(draft)`；
- `trigger(publishedId)`；
- `getStatus(runId)`；
- `delete(publishedId)`；
- URL 构造和引擎专属 schema。

## 11. 推荐目标架构

不建议立即升级 React 或把两套目录强行合并。先修一致性，再抽共性。

```text
orchestrator-core
├── GraphCanvas              React Flow 节点、边、布局、选择
├── SchemaForm               统一动态字段、校验、JSON 编辑
├── DraftState               dirty/saving/error/revision
├── DagValidator             环、未知上游、重复边、自环
└── SaveCoordinator          保存串行化、去重、并发保护

domain adapters
├── TrainingAdapter
│   ├── createNode -> POST Task
│   ├── saveNodes -> PUT dirty Tasks
│   ├── saveGraph -> PUT Pipeline
│   └── run -> Argo endpoint
└── EtlAdapter
    ├── createNode -> local draft
    ├── saveSnapshot -> POST config
    └── run -> scheduler adapter endpoint
```

关键原则：

1. Graph UI 可以共享，持久化语义不能假装相同；
2. 只有一个规范化 draft 是保存源，不再从多个 effect 和 local state 临时拼接；
3. 所有保存都返回结构化 Result/Promise；
4. 前后端共同执行 DAG 校验，后端是最终门禁；
5. 保存带 revision，冲突返回 409，不允许静默覆盖；
6. 运行必须绑定一个已成功保存的 revision；
7. 历史 `vison*` 路径和 `templte_*` 字段通过兼容层保留。

## 12. 分阶段修复路线

### 阶段 A：发布阻断项

- 修复训练 DAG 拓扑校验，并添加后端单元测试；
- 修复 ETL config 回退/规范化，禁止无意提交 `{}`；
- 让两侧 save thunk 返回 Promise，业务错误 reject；
- 运行前严格等待所有保存成功；
- 训练 Task 失败项保留 dirty，不全量 reset；
- ETL 成功提示和 `saved/editing` 仅由成功响应驱动；
- 修复 ETL 删除顺序。

验收标准：网络延迟、HTTP 失败、业务状态失败、重复点击和保存中继续编辑都不丢修改，不运行旧 revision。

### 阶段 B：后端真实性与权限

- K8s 创建异常向上传播，数据库状态与集群结果一致；
- 为 ETL config/template/submit 增加并验证对象级 project 权限；
- 明确 ETL 是仅导出配置还是负责发布/触发，补齐适配器契约；
- 把调度器 host 移到配置中心，移除占位域名；
- 实现远端发布、状态查询、删除或明确禁用对应按钮。

### 阶段 C：状态与 schema 治理

- 建立版本化 DTO 和 JSON Schema；
- 修复 falsy 初始化、全局 JSON editor owner、`crontab` 更新门槛；
- 加 revision/409 冲突处理和离开页面保护；
- 统一相对/绝对 URL 策略；
- 对 HTML/Markdown/SVG 做白名单净化。

### 阶段 D：共享基础设施

- 抽 GraphCanvas、SchemaForm、DagValidator、SaveCoordinator；
- 保留训练/ETL adapter；
- 去除复制的 ETL 引擎 schema；
- 在行为测试稳定后再评估 React、React Flow 和 Axios 升级。

## 13. 建议测试矩阵

### 13.1 前端单元测试

- DAG 序列化：孤立节点、根节点、多上游、重复边、删除节点；
- schema 表单：`false`、`0`、`''`、null、缺失字段、字典 choices、无 range；
- JSON editor：pipeline/task owner 隔离、确认、取消、非法 JSON；
- save reducer：dirty -> saving -> saved/error；
- 保存期间继续编辑：只清除已保存版本；
- URL builder：相对和绝对地址。

### 13.2 API/thunk 测试

- HTTP reject、timeout、业务 `status != 0`；
- Task 部分成功、部分失败；
- Pipeline 保存成功前不得调用 run；
- 连续两次保存响应乱序；
- ETL 未编辑全局配置时保留原 config；
- 删除保存必须使用删除后的 elements。

### 13.3 后端测试

- 训练 DAG：空、单点、链、菱形、自环、多节点环、未知上游；
- Argo 创建失败时不写成功状态；
- ETL 节点不含 `crontab` 仍能更新受前端管理字段；
- 创建者、同项目成员、异项目成员、管理员四类权限；
- revision 冲突返回 409；
- 适配器 publish/trigger/status/delete 契约测试。

### 13.4 浏览器端到端测试

- 拖入、连线、改参数、保存、刷新后完全一致；
- 删除节点后刷新不复活；
- 慢网络下点击运行只执行最新版本；
- 保存失败保持“未保存”并允许重试；
- 两个标签页同时编辑时出现冲突提示；
- 大图的拖拽、表单和保存性能。

## 14. 隔离验证记录

### 14.1 TypeScript thunk 验证

使用仓库 `myapp/frontend/node_modules/typescript` 转译两套实际 slice 文件，用内存 mock 替代 API 和 Redux dispatch。

观察结果：

```json
{
  "trainingTaskFailure": {
    "promiseStatus": "rejected",
    "dispatched": [
      "task/updateLoading",
      "task/updateLoading",
      "task/resetTaskList"
    ],
    "pendingChangesReset": true
  },
  "etlSave": {
    "thunkReturn": "undefined",
    "submittedConfig": {},
    "sourceConfig": {"retain": "must-stay"},
    "immediateActionsBeforeHttpCompletion": [
      "pipeline/updateSaved",
      "pipeline/updateSaved"
    ],
    "businessErrorStillClearsEditing": true
  }
}
```

### 14.2 Python DAG 验证

从源码 AST 提取 `order_by_upstream`，没有 import Flask/Myapp：

```text
cycle => {}
unknown_upstream => {}
valid => {'a': {}, 'b': {'upstream': ['a']}}
```

### 14.3 构建结果与未执行项

- 已按各自 `package-lock.json` 为两个编排器执行 `npm ci --legacy-peer-deps`；
- 两套 CRA 生产构建均成功，只有既有 ESLint、source map、Browserslist、CRA 维护状态和包体积警告；
- 两套测试命令均能正常启动，但因为源码中没有任何匹配的测试文件，以 `No tests found` 和退出码 1 结束；
- 本机系统 Python 3.11 没有安装完整后端包；仓库现有 `modelone/local-backend:source-clean-20261004` 镜像已确认包含 Python 3.9.25、Flask 2.3.3、Flask-AppBuilder 4.3.7 和 SQLAlchemy 1.4.49；
- 未启动依赖业务数据库、Redis 和配置文件的完整后端；
- 未连接 Kubernetes、Argo 或外部调度器；
- 权限结论未做多用户 HTTP 集成验证；
- 未做浏览器截图、交互和性能测试。

因此，报告中的“静态确认/隔离复现”问题证据充分，但真实部署还需要按第 13 节完成集成和端到端验收。

## 15. 关键文件索引

### 训练前端

- [入口](../../myapp/vision/src/index.tsx)
- [模板树](../../myapp/vision/src/components/ModuleTree/index.tsx)
- [画布](../../myapp/vision/src/components/FlowEditor/components/EditorBody/index.tsx)
- [节点表单](../../myapp/vision/src/components/FlowEditor/components/EditorBody/components/Model/index.tsx)
- [Pipeline 设置](../../myapp/vision/src/components/FlowEditor/components/EditorBody/components/Setting/index.tsx)
- [Pipeline slice](../../myapp/vision/src/models/pipeline/index.ts)
- [Task slice](../../myapp/vision/src/models/task/index.ts)
- [API](../../myapp/vision/src/api/index.ts)

### ETL 前端

- [入口](../../myapp/visionPlus/src/index.tsx)
- [模板树](../../myapp/visionPlus/src/components/ModuleTree/index.tsx)
- [画布](../../myapp/visionPlus/src/components/FlowEditor/components/EditorBody/index.tsx)
- [节点表单](../../myapp/visionPlus/src/components/FlowEditor/components/EditorBody/components/Model/index.tsx)
- [Pipeline 设置](../../myapp/visionPlus/src/components/FlowEditor/components/EditorBody/components/Setting/index.tsx)
- [Pipeline slice](../../myapp/visionPlus/src/models/pipeline/index.ts)
- [Task slice](../../myapp/visionPlus/src/models/task/index.ts)
- [API](../../myapp/visionPlus/src/api/index.ts)

### 后端

- [训练 Pipeline 视图与运行链](../../myapp/views/view_pipeline.py)
- [训练 Pipeline/Task 模型](../../myapp/models/model_job.py)
- [ETL 视图与自定义 API](../../myapp/views/view_etl_pipeline.py)
- [ETL Pipeline/Task 模型](../../myapp/models/model_etl_pipeline.py)
- [Airflow 适配器](../../myapp/views/view_etl_pipeline_airflow.py)
- [Azkaban 适配器](../../myapp/views/view_etl_pipeline_azkaban.py)
- [DolphinScheduler 适配器](../../myapp/views/view_etl_pipeline_dolphinscheduler.py)

## 16. 最终判断

训练编排器的领域链路比 ETL 完整：模板、Task、Pipeline、Argo Workflow 和 K8s 提交都已连接，但保存事务、DAG 校验和错误传播不足，导致“能运行”不等于“可靠运行”。

ETL 编排器的画布和 schema 表单已经具备可用基础，整图配置模型也便于扩展；但当前保存状态存在明确数据丢失风险，调度适配层仍是骨架，不具备真正的多调度器生命周期管理。

建议决策顺序是：先把两套保存/运行链修成可证明的一致事务，再补齐后端错误和权限边界，随后治理 schema 与 revision，最后抽取共享画布和表单。直接合并目录或先升级框架，会扩大变化面，却不能解决当前最高风险问题。
