# modelOne 空间模型设计方案（v2 单层工作空间）

日期：2026-09-22。状态：设计稿 v2，待评审。v2 决策：**项目即空间，单层模型**——不引入 space/project 两级，`project` 表直接作为工作空间表；用户可见层级只有"平台域"与"空间域"两层。本设计遵守升级兼容承诺：不改表名、不改关键 API 路径、不改 Kubernetes CRD。

## 1. 背景与问题

当前 `project` 单表承载三层语义（`myapp/models/model_team.py:26`）：`type='org'` 行携带集群/资源组/存储等基础设施绑定（`expand`，`node_selector` 属性见 model_team.py:62-73）；业务资源外键挂 `project` 并以 `project_user`（role 枚举 `dev/ops/creator`）做成员与权限边界；`type='job-template'` 等为目录类型。默认数据中业务资源直接挂在 `public`（org 行）下，菜单只暴露 org 管理入口，导致"项目空间"语义含糊、用户找不到切换入口。

v2 的立场：团队边界与工作上下文在企业实际使用中基本重合，拆两层制造管理成本而不产生价值。因此把"分裂"改为"合一"：一个空间实体同时承载成员与角色、资源绑定、配额池与资产归属。

## 2. 目标概念模型（用户可见两层）

### 2.1 平台域（无需上下文）

- 系统管理：用户、全局角色（admin 判定见 `myapp/security.py:68`）、安全设置、日志；
- 基础设施（管理员）：资源组（节点标签 `org=xx`）、集群、节点、存储类；
- 项目空间管理：空间列表、我的空间、成员与配额管理入口；
- 平台级可见：AIHub 市场浏览、文档、用户中心（先发现后进入，不被门禁）。

### 2.2 空间域（进入某个项目空间后）

- 成员与角色：`project_user` 空间行，role `dev/ops/creator`；成员 `quota`（该成员在空间内的额度上限）、`org`（成员可用资源组白名单，空=继承空间默认）；
- 资源绑定：空间 `expand` 存 `cluster`、默认资源组、`volume_mount`、`SERVICE_EXTERNAL_IP`（沿用原 org 键）；
- 配额池：`expand.quota = {gpu, cpu, memory, storage}`；
- 业务模块：数据资产、在线开发、模型训练、服务化、数据智能——全部资产外键挂该空间；
- 空间首页：资产概览、配额用量、成员入口。

### 2.3 关系图

```
ab_user ──< project_user(role/quota/org) >── project(type=space) ──< 业务资产
   │                                              │ expand: 配额池/资源绑定
   └── ab_role(全局 admin 等)
resource_group(P3 可选独立表) <── space.expand 资源绑定
```

空间内如需再分组（大团队分方向等），使用资产上的标签/分组字段，**不增加导航或实体层级**。

## 3. 数据模型变更

### 3.1 P0：`project` 表

- `type` 取值正式化：`space`（团队空间，原 `org` 及资产所挂行迁入）、目录类型 `job-template`/`model` 保留；
- **不新增列、不加 `parent_id`**；唯一约束 `(name, type)` 与索引不变；
- `expand` 语义约定（JSON 文本列不变）：space 行 `{"quota": {...}, "resource_groups": [...], "default_resource_group": "...", "cluster": ..., "volume_mount": ..., "service_external_ip": ...}`，旧 org 键保留兼容读取。

### 3.2 `project_user` 表

零结构变更。语义正式化：行即空间成员；`quota`=成员空间内上限；`org`=成员资源组白名单。

### 3.3 迁移策略（扩展 `scripts/migrate_modelone.py`）

一条幂等规则：`type='org'`、或被业务资产外键引用、或存在 `project_user` 成员行的记录 → `type='space'`；目录类型不动；名称冲突（同名 space 与目录行）以 type 区分，唯一约束已覆盖。迁移前备份（复用 backup_modelone.py 校验和流程），重跑跳过已达标行，回退=恢复备份。

## 4. 角色与权限

| 层级 | 角色 | 能力 |
|---|---|---|
| 平台 | admin | 系统管理、基础设施、全空间只读+干预 |
| 空间 | creator | 空间设置、配额池、成员管理（现状 view_team.py:101 校验保留）、空间内全部管理操作 |
| 空间 | ops | 部署/运维类操作 |
| 空间 | dev | 开发类操作（Notebook/Pipeline/训练等） |
| 空间 | observer（P3 可选） | 只读 |

权限过滤在 `Project_Join_Filter`/`get_join_projects_id`（security.py:375）上延续，无继承规则需要（单层）。

## 5. 上下文与 API 约定

### 5.1 客户端

- localStorage 单键 `modelone_current_space`（旧键 `modelone_current_project` 读时自动迁移改名）；
- 顶栏切换器即空间切换器：选项=已加入的 `type='space'` 行 + 「全部空间」（仅平台 admin 与空间 creator 可见的显式跨空间上下文）；
- 无上下文=仅平台域菜单。

### 5.2 服务端（P1 端点、P2 收口）

- `POST/GET /myapp/context`：`{space_id}`，校验成员资格后写入 flask session；退出清理；
- 含 `project` 外键的模型列表 API：无显式 `form_data.filters.project` 时按会话空间收口；
- `_info` 增加 `"context_required": true`（业务模型），前端路由守卫无上下文重定向到空间入口页；
- SDK/脚本：`X-Modelone-Context: space=<id>` 头等效 session（P2）；
- 现切换器在 `ADUGTemplate.formatFilterParams` 的客户端注入（feat(ui) 引入）于 P2 删除，收口服务端化。

## 6. 信息架构与导航门禁

菜单仍服务端下发（`myapp/views/home.py`），按会话上下文裁剪：

| 上下文 | 菜单 |
|---|---|
| 无 | 平台管理、基础设施、项目空间管理（空间列表/我的空间）、AIHub 市场浏览、文档、用户中心 |
| 有空间 | + 空间首页 + 数据资产、在线开发、模型训练、服务化、数据智能 |

- URL 保持 `/frontend/<group>/<sub>/<page>` 不变；上下文不经 URL 传递，深链 `?space=` 于 P2 补充；
- 全局 Home 改为着陆/重定向页：有上下文→空间首页，无→空间列表；
- 「全部空间」上下文下业务组可见、列表跨空间展示、页头显示跨空间标识。

## 7. 配额治理（两级）

- 空间池（expand.quota）→ 成员上限（project_user.quota）；
- 校验点（P2）：Notebook/推理/训练创建钩子累加在跑资源请求，先对成员 quota、再对空间池，取最严拒绝并返回可读错误；
- 用量统计复用 `pod_modelview` 计量按空间聚合，空间首页展示；
- 调度落点不变：`node_selector` 继续由空间 expand 生成。

## 8. 分期实施与验收

### P0 模型与管理入口

任务：migrate_modelone 单规则改型迁移；空间列表/成员与配额管理页进菜单（复用通用 ADUG + related_views）；切换器选项改读 type='space'；回归扩展（迁移幂等/回退、角色单测）。
验收：MySQL 样本库迁移幂等+备份回退演练；34 项品牌/发布回归、业务接口验证、品牌扫描全过；现切换器功能不回归。

### P1 入口与导航门禁

任务：`/myapp/context` 单值上下文；菜单上下文裁剪；空间首页；`_info.context_required` 与路由守卫；旧 localStorage 键迁移；用户/升级手册更新。
验收：无上下文访问业务页重定向；两种上下文菜单快照测试；认证回归与代理联测复跑。

### P2 服务端收口与配额

任务：baseApi 上下文默认过滤、删除客户端注入、两级配额校验、空间首页用量、`X-Modelone-Context` 头、深链参数。
验收：绕过前端直调 API 仍收口；配额越界创建被拒；SDK 示例更新。

### P3 可选加固

任务：resource_group 独立表（expand 迁移+兼容回退读）、observer 角色、上下文切换审计、SSO 角色→空间角色映射、按空间 namespace 可选项。
验收：旧配置自动迁移；审计可查；企业认证回归。

每期独立提交序列与发布说明条目；任一期可暂停不破坏已交付态。

## 9. 兼容与风险

- 表名/API 路径/CRD 不变；「项目空间」菜单组名保留；
- P1 菜单裁剪属行为变更：升级手册标注，提供 `MODELONE_LEGACY_MENU=1` 过渡开关（一个版本周期）；
- P2 改变列表 API 默认返回集：显式 `form_data` 过滤始终优先；发布说明与 API 文档标注；
- 企业历史库先于备份副本跑 P0 迁移并核对计数；
- UI 术语维持「项目/项目组」既有称呼还是改称「空间」，由产品定（表名与 API 不受影响）。

## 10. 开放决策点

1. UI 术语：空间 vs 项目（建议：入口列表称"项目空间"，条目称"空间"，切换器标签"当前空间"）；
2. 配额口径：申请量管控 vs 实际用量展示（建议：申请量管控+用量展示）；
3. 「全部空间」跨空间上下文可见范围（建议：平台 admin + 空间 creator）；
4. 空间首页指标卡片最小集（建议：资产计数、配额用量、成员数、在跑任务数）；
5. 是否与企业 SSO 组织单元同步成员（P3，建议手动+可选同步）。
