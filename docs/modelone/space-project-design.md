# modelOne 多空间多团队模型设计方案

日期：2026-09-22。状态：设计稿，待评审。范围：项目空间语义拆分、导航门禁、服务端上下文与配额治理的 target 模型及分期实施路径。本设计遵守升级兼容承诺：不改表名、不改关键 API 路径、不改 Kubernetes CRD。

## 1. 背景与问题

当前 `project` 单表承载三层语义（`myapp/models/model_team.py:26`）：

- `type='org'`（项目分组）：携带 `expand` 中的 `cluster`、`org`（资源组）、`volume_mount`、`SERVICE_EXTERNAL_IP`，`node_selector` 属性（model_team.py:62-73）将其拼为节点标签，决定工作负载落点——**资源空间语义**；
- 业务资源（Notebook、Pipeline、数据集、模型、推理、问答配置）外键挂 `project`，成员与角色经 `project_user`（role 枚举 `dev/ops/creator`，model_team.py:213 附近）过滤——**团队空间语义**；
- `type='job-template'` 等：任务模板分类目录，与上述两者无关。

默认初始化数据进一步混淆：业务资源直接挂在 `public`（本身是 org）下；菜单只暴露 org 层管理入口，业务项目层无列表页。后果：用户找不到"切换项目"的入口；资源归属、团队边界、基础设施绑定三个正交概念无法独立演进。

## 2. 目标概念模型（四域）

### 2.1 平台域（系统管理，无需上下文）

用户与全局角色（`ab_user`/`ab_role`，admin 判定见 `myapp/security.py:68`）、安全设置、日志审计、平台级 AIHub 市场浏览、文档与用户中心。

### 2.2 基础设施域（平台管理员）

资源组（节点标签 `org=xx`）、集群、节点、存储类。当前寄居在 org 行 `expand` 中，target 为独立 `resource_group` 表（P3）。

### 2.3 空间域 space（团队/部门）

- 成员与空间角色（复用 `project_user`，space 行）；
- 配额池：`{gpu, cpu, memory, storage}` 总量；
- 默认资源组绑定（可多个，含权重/用途）；
- 空间首页：项目列表、配额用量、成员与角色、公告位（预留）。

### 2.4 项目域 project（空间内的工作上下文）

- 隶属空间（`parent_id`）；成员继承空间成员可见性，项目级 `project_user` 行覆写角色；
- 项目配额：不超过空间池的分额；资源组覆写（可选，默认继承空间）；
- 业务资产唯一归属层：所有含 `project` 外键的模型不变。

### 2.5 关系图

```
ab_user ──< project_user >── project(type=space) ──< project(type=project) ──< 业务资产
   │            │ quota/org        │ expand: 配额池/默认资源组     │ expand: 分额/资源组覆写
   │            └── space 行=空间成员，project 行=项目成员（覆写）
   └── ab_role(全局: admin 等)
resource_group(P3 独立表) <── space.默认资源组 / project.覆写
```

## 3. 数据模型变更

### 3.1 P0：`project` 表

- `type` 取值正式化：`space`（原 `org` 迁移）、`project`（业务项目）、`job-template`、`model` 等目录类型保留；
- 新增 `parent_id = Column(Integer, ForeignKey('project.id'), nullable=True)`：`type='project'` 行必填，指向 space；space 行为 NULL；
- `expand` 语义约定（P0 仍为 JSON 文本，不改列）：
  - space 行：`{"quota": {...}, "resource_groups": ["<name>..."], "default_resource_group": "<name>", "cluster": ..., "volume_mount": ..., "service_external_ip": ...}`（继承原 org 键，旧键保留兼容读取）；
  - project 行：`{"quota": {...}, "resource_group": "<name>"}`（可选覆写）；
- 唯一约束 `(name, type)` 保留；新增索引 `parent_id`。

### 3.2 P0：`project_user` 表

不新增列。语义正式化：

- `project_id` 指向 space 行 = 空间成员；指向 project 行 = 项目成员（角色覆写）；
- `quota`：空间行=该成员在空间的额度上限；项目行=在该项目内的上限（≤空间行）；
- `org`：成员可用资源组白名单（空=继承空间默认）。

### 3.3 P3：`resource_group` 新表（target，仅预告）

`id, name, cluster_name, node_labels(JSON), volume_mount, service_external_ip, describe`；space/project `expand` 中相应键迁移为外键引用；迁移前 `expand` 读取保持兼容回退。

### 3.4 迁移策略（扩展 `scripts/migrate_modelone.py`）

- `type='org'` → `type='space'`；
- 被业务资产引用、或 `type` 为空/其他非目录类型的行 → `type='project'`，`parent_id` 指向默认 space（无则创建名为 `public` 的 space，沿用原 `public` org 行改型）；
- `type='job-template'/'model'` 目录行不动；
- 幂等：以 `(type, parent_id)` 目标态判定跳过；回退：迁移前备份表（复用 backup_modelone.py 校验和流程）；
- 展示字段品牌迁移管线不变，本迁移仅结构语义。

## 4. 角色与权限继承

| 层级 | 角色 | 能力 |
|---|---|---|
| 平台 | admin（ab_role） | 系统管理、基础设施、所有空间只读+干预 |
| 空间 | creator | 空间设置、配额池、项目增删、项目 creator 等效、成员管理 |
| 空间 | ops | 空间内所有项目 ops 等效（部署/运维类操作） |
| 空间 | dev | 仅可见空间与项目列表；操作需项目成员身份 |
| 项目 | creator/ops/dev | 现状语义不变（creator 管成员，见 view_team.py:101 校验） |
| 项目 | observer（P3） | 只读 |

继承规则：空间 creator/ops 在空间内全部项目自动获得等效角色，无需逐项目加成员；项目行存在时以项目行为准（覆写而非叠加）。权限过滤在 `Project_Join_Filter`/`get_join_projects_id`（security.py:375）基础上扩展空间继承分支。

## 5. 上下文与 API 约定

### 5.1 客户端

- localStorage：`modelone_current_space`、`modelone_current_project`（旧键 `modelone_current_project` 读时自动迁移：若其 id 对应 type='project' 行则补写 space）；
- 顶栏级联切换器：空间下拉 → 项目下拉；平台管理员/空间 creator 额外可选「全部项目」（显式跨项目上下文，值 `project=0` 且要求空间已选）；
- 无上下文 = 仅平台域菜单。

### 5.2 服务端（P1 端点、P2 收口）

- `POST /myapp/context`：`{space_id, project_id}`，校验成员资格后写入 flask session；`GET /myapp/context` 回读；退出登录清理；
- 列表 API（`MyappModelRestApi`）：存在 `project` 外键的模型，无显式 `form_data.filters.project` 时按会话上下文 project 收口；空间级页面按 space 收口；
- `_info` 增加 `"context_required": true`（业务模型）与 `"context_scope": "space"|"project"`；前端路由守卫据此重定向到入口页；
- SDK/脚本：`X-Modelone-Context: space=<id>;project=<id>` 头等效 session（P2），任务令牌沿用现有用途限制机制。

### 5.3 与现切换器的关系

P0 期间现切换器改读 `type='project'`（限定已加入空间）继续工作；P1 被级联切换器+会话上下文取代；P2 删除 `ADUGTemplate.formatFilterParams` 中的客户端注入逻辑（本次 feat(ui) 引入），收口完全服务端化。

## 6. 信息架构与导航门禁

菜单仍由 `myapp/views/home.py` 服务端下发，按会话上下文裁剪：

| 上下文 | 菜单 |
|---|---|
| 无 | 平台管理（用户/角色/日志/安全设置）、基础设施（资源组/集群/节点）、空间管理（空间列表、我的空间）、AIHub 市场浏览、文档、用户中心 |
| space | + 空间首页（项目卡片、配额用量、成员入口） |
| project | + 数据资产、在线开发、模型训练、服务化、数据智能（全部业务组） |

- 平台域不被门禁：AIHub 市场浏览、文档、用户中心始终可见（先发现后进入）；
- 「全部项目」上下文下业务组可见但列表跨项目展示，页头显示醒目的跨项目标识；
- 入口页：空间首页/项目首页复用 Home 组件模式（卡片+列表），全局 Home 改为着陆/重定向页（有上下文→项目首页，无→空间列表）；
- URL 保持 `/frontend/<group>/<sub>/<page>` 不变（兼容承诺），上下文不经 URL 传递；深链支持以 `?space=&project=` 查询参数在 P2 补充。

## 7. 配额与资源治理

- 校验点（P2）：Notebook/推理/训练创建钩子累加在跑资源请求 vs 项目分额 vs 空间池 vs 成员 quota，三级取最严；超限拒绝并返回可读错误；
- 调度落点不变：`node_selector` 继续由 space/project `expand`（P3 后 resource_group）生成；
- 用量统计（P2）：复用 `pod_modelview` 计量数据按 project 聚合，空间首页展示；
- 按项目 K8s namespace（P3 可选）：现 namespace 为全局配置（model_team.py:76-82），开启后按 project 名生成并纳入升级手册的兼容说明。

## 8. 分期实施与验收

### P0 模型与管理入口

任务：Alembic 迁移（parent_id+索引+type 改值）、migrate_modelone 数据改型、空间/项目列表与成员配额管理页进菜单（复用通用 ADUG + related_views）、切换器改读 type='project'、回归扩展（迁移幂等/回退、成员继承单测）。
验收：MySQL 样本库迁移幂等+备份回退演练；34 项品牌/发布回归、业务接口验证、品牌扫描全过；现切换器功能不回归。

### P1 入口与导航门禁

任务：`/myapp/context` 端点与 session、级联切换器、菜单上下文裁剪、空间/项目首页、`_info.context_required` 与路由守卫、旧 localStorage 迁移、用户手册/升级手册更新。
验收：无上下文访问业务页重定向；三种上下文菜单快照测试；认证回归七项与代理联测复跑。

### P2 服务端收口与配额

任务：baseApi 上下文默认过滤、删除客户端注入、配额三级校验、空间首页用量、`X-Modelone-Context` 头、深链参数。
验收：绕过前端直调 API 仍收口；配额越界创建被拒且错误可读；SDK 示例更新。

### P3 基础设施分离与加固

任务：resource_group 表与 expand 迁移、namespace 可选项、observer 角色、上下文切换审计日志、SSO 角色→空间角色映射规则。
验收：旧 expand 配置自动迁移并保留回退读；审计查询可用；企业认证回归。

每期独立提交序列（feat/migrate/ui/docs 分离）、独立发布说明条目；任一期可暂停而不破坏已交付态。

## 9. 兼容与风险

- 表名/API 路径/CRD 不变；菜单名称保留「项目空间」组名至 P1 后视用户反馈再议；
- P1 菜单裁剪对已部署环境属行为变更：升级手册标注，并提供 `MODELONE_LEGACY_MENU=1` 过渡开关（一个版本周期）；
- P2 改变列表 API 默认返回集：`form_data` 显式过滤始终优先；发布说明与 API 文档标注；
- 存量数据：企业历史库迁移先跑 P0 迁移于备份副本并核对计数（沿用验收记录中的演练流程）；
- 前端构建产物与品牌门禁不受影响；新增页面全部读取统一品牌配置。

## 10. 开放决策点（需产品确认）

1. 空间与部门的对应关系：是否与企业通讯录/SSO 组织单元自动同步（影响 P3 映射规则）；
2. 跨空间共享资产（公共数据集/公共模型库）是否需要平台级"公共空间"实体，还是以 AIHub 市场承载；
3. 配额计量口径：申请量 vs 实际用量，GPU 是否按卡型加权；
4. 「全部项目」跨项目上下文是否仅平台 admin 可见，还是空间 creator 亦可见；
5. 项目首页/空间首页的信息密度与卡片指标清单。
