# Cube-Studio LICENSE 合规分析报告

> 分析日期：2026年9月21日  
> 分析对象：仓库根目录 `LICENSE` 及相关依赖、构建和镜像交付配置  
> 文件位置：`/Users/zhaoxiaogang/Documents/同步空间/04 项目管理/coding/人工智能平台/cube-studio/LICENSE`  
> 说明：本报告用于开源合规工程分析，不构成针对具体交易、争议或司法辖区的正式法律意见。

## 1. 结论摘要

Cube-Studio 项目本体当前声明采用 **MIT License**，版权声明为：

```text
Copyright (c) 2021 Tencent Music Entertainment Group
```

MIT 许可证允许任何人免费使用、复制、修改、合并、发布、分发、再许可和销售软件副本。因此，项目本体原则上可以用于内部部署、私有化部署、二次开发、商业销售和闭源产品集成。

使用或分发时最核心的项目本体义务是：

> 在软件的所有副本或实质性部分中保留原版权声明和 MIT 许可声明。

但是，仓库根 `LICENSE` 并不只包含 Cube-Studio 本体的 MIT 文本。该文件共约 1,372 行，还拼接了多个第三方组件的归属信息和许可证全文，包括：

- MIT；
- Apache License 2.0；
- BSD 2-Clause；
- Modified BSD；
- BSD 3-Clause；
- GNU LGPL 2.1；
- Eclipse Public License 2.0。

因此，需要区分两个层面：

1. **Cube-Studio 自有代码**：以文件开头的 MIT License 为项目许可声明。
2. **随项目源代码、静态资源、安装脚本或镜像分发的第三方内容**：继续受各自原始许可证约束。

当前主要合规问题不是项目能否商用，而是第三方许可证材料能否准确、完整地随最终交付物提供。当前根 `LICENSE` 已出现清单不完整、名称不准确、部分组件版本和版权信息过时、镜像未复制许可证文件等问题。

综合判断：

| 项目 | 结论 |
|---|---|
| 项目本体许可 | MIT，宽松许可 |
| 商业使用 | 允许 |
| 闭源二次开发 | 原则上允许，但须满足第三方组件义务 |
| 修改后再分发 | 允许，须保留 MIT 声明 |
| 销售软件或服务 | 允许 |
| 项目本体源码公开义务 | MIT 本身不要求公开修改源码 |
| 明示专利授权 | MIT 文本没有 Apache-2.0 式的明确专利授权条款 |
| 第三方许可证管理 | 当前存在明显改进空间 |
| Docker／离线交付合规 | 当前存在许可证材料可能未随镜像交付的风险 |

## 2. 文件结构分析

### 2.1 项目本体 MIT 声明

`LICENSE` 第 1～21 行是标准 MIT 许可证文本，包含以下权利：

- 使用；
- 复制；
- 修改；
- 合并；
- 发布；
- 分发；
- 再许可；
- 销售软件副本。

其条件是保留版权声明和许可声明。

MIT 文本还包含完整的“按现状提供”免责声明，明确排除适销性、特定用途适用性和不侵权等明示或默示保证，并限制作者和版权人的责任。

### 2.2 第三方许可证材料

从第 25 行开始，文件进入 `Other dependencies and licenses`，之后罗列第三方软件及许可证。

| LICENSE 区域 | 声明的组件或内容 |
|---|---|
| 28～84 行 | React、Redux Toolkit、Axios、Moment、React Router 等 MIT 组件 |
| 87～285 行 | TypeScript、Kubeflow、Prometheus、Grafana、Volcano、Kaldi、XGBoost 等 Apache-2.0 内容 |
| 288 行之后 | TensorFlow 及其第三方材料 |
| 381 行之后 | TypeScript ESLint 的 BSD 2-Clause 声明 |
| 411 行之后 | Jupyter 的 Modified BSD 声明 |
| 480 行之后 | PyTorch 的 BSD 3-Clause 声明 |
| 561 行之后 | scikit-learn、SciPy、Pandas、NumPy 等 BSD 3-Clause 声明 |
| 621 行之后 | Gensim 对应的 LGPL 2.1 文本 |
| 1089 行之后 | Theia 对应的 EPL 2.0 文本 |

第三方许可证全文出现在根 `LICENSE` 中，不等于整个 Cube-Studio 项目同时被这些许可证共同许可。它们的作用主要是记录随项目使用或分发的第三方内容及其原始许可条件。

但当前文件没有清楚说明每一项第三方许可证具体覆盖哪些仓库目录、二进制文件、容器层或静态资源，容易让使用者误以为整个项目是多许可证共同许可。

## 3. MIT 对使用者的影响

### 3.1 允许的行为

对于 Cube-Studio 自有 MIT 代码，使用者可以：

- 免费内部使用；
- 部署到企业内部环境；
- 修改源代码；
- 创建衍生产品；
- 将代码整合到商业产品；
- 对修改版本收费；
- 以源代码或二进制形式分发；
- 使用其他许可证发布自己的新增代码；
- 不公开自己的修改代码。

README 中“MIT，开源免费商用”的描述与项目本体 MIT 文本基本一致，但“可商用”不代表没有任何合规义务，也不代表第三方组件全部按 MIT 许可。

### 3.2 必须履行的义务

在分发 Cube-Studio 的副本或实质性部分时，应保留：

```text
MIT License

Copyright (c) 2021 Tencent Music Entertainment Group

[完整 MIT 许可文本]
```

适用场景包括：

- 发布源代码压缩包；
- 发布修改后的 Git 仓库；
- 交付私有化安装包；
- 交付包含项目代码的 Docker 镜像；
- 发布编译后的前端静态资源；
- 向客户交付离线部署介质。

许可证通常可以放在交付包根目录、产品法律声明页面或第三方声明目录中，但需要保证接收者能够合理获得。

### 3.3 不要求的事项

MIT 本身不要求：

- 公开修改后的源代码；
- 将衍生产品继续按 MIT 开源；
- 免费提供商业产品；
- 披露商业业务逻辑；
- 将新增代码贡献回原项目。

### 3.4 专利和商标边界

MIT 文本没有像 Apache License 2.0 那样单独列出明确的专利许可条款。对于高度关注专利风险的商业项目，仅凭 MIT 文本不应推导出与 Apache-2.0 完全相同的明示专利保护。

此外，软件著作权许可不应被自动理解为对 `Tencent Music Entertainment Group`、`Cube-Studio`、产品 Logo 或其他商标的授权。对外销售、重新命名或进行联合品牌宣传时，应另外核对商标和品牌使用权限。

## 4. 第三方许可证的主要义务

### 4.1 Apache License 2.0

Apache-2.0 组件允许商业使用、修改和分发，并提供明确的贡献者专利授权，但再分发时通常需要：

- 向接收者提供 Apache-2.0 许可证文本；
- 对被修改的 Apache 文件作显著修改说明；
- 保留适用的版权、专利、商标和归属声明；
- 如果上游组件带有 `NOTICE`，在衍生分发中保留适用的 NOTICE 内容；
- 不把上游商标许可理解为产品背书权。

仓库包含或引用的 Apache-2.0 组件包括 TypeScript、TensorFlow、Kubeflow、Prometheus、Grafana、Volcano、XGBoost 等。具体义务是否触发，取决于交付物中是否实际包含相应源码、二进制、配置文件或镜像层。

### 4.2 BSD 2-Clause 和 BSD 3-Clause

BSD 许可证通常允许闭源和商业分发，但要求：

- 源代码分发时保留版权、条件和免责声明；
- 二进制分发时在文档或其他材料中复制相关声明；
- BSD 3-Clause 组件还通常禁止未经许可使用原作者或组织名称为衍生产品背书。

根 `LICENSE` 中的 Jupyter、PyTorch、scikit-learn、SciPy、Pandas、NumPy 等内容属于这一类。

### 4.3 LGPL 2.1

根 `LICENSE` 将 Gensim 列为 LGPL 2.1 组件，仓库的深度学习 Notebook 镜像 Dockerfile 也确实执行了 `pip install ... gensim ...`。

LGPL 允许与非自由软件组合，但在分发包含 LGPL 库的产品或镜像时，应特别核对：

- 提供 LGPL 许可证文本；
- 保留库的版权和许可声明；
- 向接收者提供或说明如何获得对应库源码；
- 如果修改了 LGPL 库，公开该库修改部分的对应源码；
- 保证用户能够替换或重新链接到兼容的修改版库，具体方式取决于动态链接、静态链接和运行环境。

Python 通过普通包方式导入通常比静态链接的本地二进制更容易满足“可替换库”要求，但最终仍应根据实际镜像内容、安装方式和是否修改过依赖进行核查。

### 4.4 EPL 2.0

根 `LICENSE` 将 Theia 列为 EPL 2.0 组件。仓库中存在 Theia 镜像构建文件，会构建并复制 Theia 应用内容。

如果对外分发包含 EPL Program 的镜像，应重点保证：

- EPL Program 的源码可通过合理方式获得；
- 说明源码按 EPL 2.0 提供以及获取方式；
- 源码形式分发时包含 EPL 2.0 文本；
- 不删除原版权、专利、商标、归属和免责声明；
- 如果修改 EPL 覆盖的源文件，按 EPL 处理这些修改。

EPL 的要求主要作用于 EPL Program 和其 Modified Works，不应在没有具体代码边界分析的情况下直接推导为整个 Cube-Studio 必须按 EPL 开源。

## 5. 当前仓库的主要合规发现

### 5.1 高风险：最终 Docker 镜像没有明确携带许可证材料

后端镜像 `install/docker/Dockerfile` 主要复制：

```text
myapp
myapp/static/appbuilder/frontend
aihub
entrypoint.sh
```

前端镜像 `install/docker/dockerFrontend/Dockerfile` 主要复制：

```text
myapp/static/appbuilder/frontend
myapp/static
Nginx 配置
```

两个 Dockerfile 均没有明确复制仓库根 `LICENSE`、第三方声明文件或源码获取说明。

这意味着：

- Git 源码仓库包含 `LICENSE`；
- 但最终镜像中未必存在 Cube-Studio MIT 文本；
- 前端 Bundle 中的第三方依赖声明未必随静态产物提供；
- Theia、Gensim、Apache 和 BSD 组件的许可证材料可能只存在于源码仓库，不存在于对外镜像交付物。

如果这些镜像会被推送给客户、合作方或公共镜像仓库，建议视为优先整改项。

### 5.2 高风险：第三方清单与当前实际依赖不一致

根 `LICENSE` 的第三方清单明显不是当前完整的依赖清单。

例如主前端当前直接依赖还包括：

- Ant Design；
- ECharts；
- D3；
- d3-graphviz；
- highlight.js；
- Less；
- Long；
- CodeMirror；
- Three.js；
- Webpack；
- Workbox；
- KaTeX；
- Markdown-It。

其许可证不仅包含 MIT 和 Apache-2.0，还包括 BSD-2-Clause、BSD-3-Clause、ISC、CC0-1.0 和 Unlicense 等。当前根 `LICENSE` 未形成与锁文件相匹配的完整第三方清单。

Python 侧也存在同样问题：`install/docker/requirements.txt` 和 Notebook 镜像依赖包含数十到数百个 Python 包，而根 `LICENSE` 只列出其中少量组件。

### 5.3 中高风险：第三方组件名称和版权信息存在错误或歧义

当前文件中的典型问题包括：

- `react` 被重复列出，其中一项写成 Microsoft Corporation，疑似原本想表示 Fluent UI 或其他 Microsoft 组件；
- `toolkit` 名称过于模糊，可能指 `@reduxjs/toolkit`；
- `DefintelyTyped` 拼写错误，应为 DefinitelyTyped；
- `nni` 的版权信息中出现 `MicrosoftRevision`，疑似文本拼接错误；
- 部分组件版权年份停留在 2021 年；
- 部分声明只写项目名称，没有精确版本、包名、来源和适用目录。

这些问题不会自动改变第三方软件原有许可证，但会降低归属清单的准确性，使商业交付难以证明已完成合理的开源合规审查。

### 5.4 中风险：项目许可证和第三方声明混在一个文件中

根文件同时承担：

1. Cube-Studio 项目本体许可证；
2. 第三方依赖清单；
3. 多个第三方许可证全文；
4. TensorFlow 第三方材料；
5. LGPL 和 EPL 全文。

这种结构使项目本体许可边界不够清楚，也不利于自动化许可证扫描工具解析。

建议调整为：

```text
LICENSE
THIRD_PARTY_NOTICES.md
licenses/
├── Apache-2.0.txt
├── BSD-2-Clause.txt
├── BSD-3-Clause.txt
├── LGPL-2.1.txt
└── EPL-2.0.txt
```

其中：

- `LICENSE` 只保留项目本体 MIT 文本；
- `THIRD_PARTY_NOTICES.md` 记录组件、版本、来源、许可证、版权和适用交付物；
- `licenses/` 存放需要随分发提供的第三方许可证全文。

在未确认所有历史交付兼容性前，不建议直接删除当前根 `LICENSE` 后半部分。应先生成准确的替代文件，再迁移并验证镜像内容。

### 5.5 中风险：前端编译产物被纳入仓库，但缺少对应第三方声明

仓库跟踪了 `myapp/static/appbuilder` 下的大量编译后静态文件、字体、JavaScript 和前端 Bundle。这些文件包含或来源于：

- React 生态依赖；
- Fluent UI 字体；
- Bootstrap；
- Marked；
- Font Awesome；
- Datepicker；
- Flask-AppBuilder 静态资源。

部分文件保留了源码头部许可声明，但压缩、打包或字体文件不一定保留全部声明。因此，仅依靠源码文件中的注释不能保证二进制或静态资源分发符合所有归属要求。

### 5.6 中风险：缺少自动化 SBOM 和许可证门禁

没有发现统一的：

- 软件物料清单 SBOM；
- Node 依赖许可证报告；
- Python 依赖许可证报告；
- 容器镜像软件清单；
- 禁止许可证策略；
- CI 许可证差异检查；
- 第三方 NOTICE 自动生成流程。

依赖持续升级后，手工维护根 `LICENSE` 很容易与实际构建结果偏离。

## 6. Git 历史中的许可证变化

Git 历史显示：

1. 2024年7月2日 11:06 的初始提交只包含 Apache License 2.0 和简短 README。
2. 2024年7月2日 11:27 的下一次提交将根许可证改为 MIT，并加入当前较长的第三方声明。
3. 主要源码在之后的 `添加基础源码` 提交中进入仓库。

因此，从当前仓库提交顺序看，主要代码是在根许可证切换到 MIT 后才导入的，没有直接显示“已按 Apache-2.0 发布的大量项目源码随后被单方面改成 MIT”的过程。

但这只能说明当前 Git 仓库中的提交顺序，不能单独证明所有导入文件的原始权属和重新许可授权。对于来自 Kubeflow、Flask-AppBuilder、Theia、TensorFlow、Jupyter 或其他上游项目的文件，仍应根据具体文件头、上游仓库和原始许可证分别处理。

## 7. 不同使用场景的合规要求

### 7.1 仅内部使用

如果企业只在内部部署、不向外部分发软件或镜像，MIT、BSD、Apache 等许可证的分发义务通常不会以相同程度触发。

但仍建议：

- 保留所有许可证文件；
- 不删除源码头部声明；
- 记录第三方组件；
- 对内部镜像保留许可证目录；
- 关注 LGPL、EPL 组件的修改和内部镜像流转方式。

### 7.2 提供 SaaS 服务

仅通过网络提供服务、未向客户交付软件副本时，MIT、Apache、BSD、LGPL-2.1 和 EPL-2.0 一般不包含类似 AGPL 的网络服务源码公开触发条款。

但是，如果同时提供客户端下载、Agent、SDK、容器镜像、离线包或边缘节点安装包，这些具体交付物仍属于分发范围，需要单独完成许可材料交付。

### 7.3 私有化交付 Docker 镜像

该场景是当前仓库最需要重视的场景。建议镜像至少包含：

```text
/usr/share/licenses/cube-studio/LICENSE
/usr/share/licenses/cube-studio/THIRD_PARTY_NOTICES.md
/usr/share/licenses/cube-studio/licenses/*
```

并在交付文档中说明：

- Cube-Studio 项目本体采用 MIT；
- 第三方软件继续适用各自许可证；
- LGPL／EPL 组件对应源码的获取方式；
- Apache NOTICE 的保留方式；
- 客户可在哪里查看完整许可证材料。

### 7.4 二次开发后闭源销售

项目本体 MIT 允许闭源销售，但应：

- 保留原 MIT 版权和许可文本；
- 不删除第三方声明；
- 将自己的版权声明与原声明并列，而不是覆盖原声明；
- 单独审查修改或打包的 LGPL 和 EPL 组件；
- 不宣称拥有第三方项目的全部版权；
- 不未经授权使用上游组织名称或商标进行产品背书。

## 8. 建议整改方案

### 8.1 P0：让许可证材料进入每一种正式交付物

修改后端和前端 Dockerfile，将以下材料复制到镜像：

```text
LICENSE
THIRD_PARTY_NOTICES.md
licenses/
SBOM/
```

并验证：

- 后端镜像；
- 前端镜像；
- Notebook 镜像；
- Theia 镜像；
- 训练和推理基础镜像；
- 离线安装包；
- Helm／Kubernetes 交付包。

### 8.2 P0：生成基于实际构建结果的第三方清单

分别对以下对象生成清单：

- 三个 Node.js 前端工程；
- 后端 Python 环境；
- Notebook Python 环境；
- Theia Node.js 环境；
- 每个正式发布的容器镜像；
- 仓库内直接复制的第三方静态文件。

清单字段建议包括：

| 字段 | 示例 |
|---|---|
| 组件 | `react` |
| 版本 | `17.0.2` |
| 许可证 | `MIT` |
| 来源 | npm／PyPI／上游 Git 仓库 |
| 版权 | 上游声明 |
| 使用位置 | frontend／vision／某镜像 |
| 是否修改 | 是／否 |
| 源码获取方式 | URL 或随包目录 |
| NOTICE 要求 | 是／否 |

### 8.3 P1：拆分项目许可证和第三方声明

推荐结构：

```text
LICENSE                     # Cube-Studio MIT
THIRD_PARTY_NOTICES.md      # 所有交付组件清单
licenses/                   # 第三方许可证全文
sbom/
├── backend.cdx.json
├── frontend.cdx.json
├── vision.cdx.json
├── vision-plus.cdx.json
└── image-*.spdx.json
```

### 8.4 P1：对 LGPL 和 EPL 组件建立专项流程

对 Gensim 和 Theia 至少确认：

- 实际发布版本；
- 是否做过源码修改；
- 是否存在静态链接或打包复制；
- 源码如何提供；
- 许可证和版权材料是否进入镜像；
- Theia 插件是否另有许可证；
- 基础镜像中是否还有其他 Copyleft 组件。

### 8.5 P1：在 CI 中建立许可证门禁

建议 CI 至少执行：

1. 生成 Node 和 Python 依赖许可证报告。
2. 对依赖许可证建立允许、复核、禁止三类策略。
3. 比较本次构建和上一版本的许可证差异。
4. 新增 LGPL、EPL、GPL、AGPL、SSPL 或未知许可证时阻断构建并要求人工复核。
5. 生成 CycloneDX 或 SPDX SBOM。
6. 验证镜像中存在许可证目录。
7. 验证 `THIRD_PARTY_NOTICES.md` 与锁文件版本一致。

### 8.6 P2：清理声明错误

应重点修正：

- 重复和错误的 React 声明；
- `toolkit` 的准确包名；
- DefinitelyTyped 拼写；
- NNI 版权文本；
- 缺失的版本号；
- 过时的年份和作者信息；
- 许可证文本与实际组件许可证不一致的问题。

## 9. 推荐的发布检查表

每次正式发布前应确认：

- [ ] 根 `LICENSE` 包含正确的 Cube-Studio MIT 文本。
- [ ] `THIRD_PARTY_NOTICES.md` 已根据锁文件和镜像更新。
- [ ] Node、Python、操作系统包和静态资源均已纳入扫描。
- [ ] 所有 Apache NOTICE 已按适用范围保留。
- [ ] BSD 版权和免责声明已进入二进制交付材料。
- [ ] LGPL 组件源码获取方式已提供。
- [ ] EPL Program 源码获取说明已提供。
- [ ] 镜像中存在完整许可证目录。
- [ ] 离线包中存在完整许可证目录。
- [ ] 未知许可证依赖已经人工处理。
- [ ] 产品文档没有把第三方内容错误描述为自有版权。
- [ ] 产品品牌宣传没有暗示上游项目或组织为产品背书。

## 10. 最终判断

Cube-Studio 项目本体使用 MIT License，许可证宽松，支持免费使用、商业使用、修改、再分发和闭源集成。README 所称“MIT、免费商用”对项目自有代码而言基本成立。

当前真正需要治理的是第三方软件合规：根 `LICENSE` 已经尝试集中记录第三方许可证，但它是一个历史性的手工清单，与当前前端依赖、Python 依赖、静态资源和容器镜像之间存在明显偏差；正式 Docker 镜像又没有明确复制许可证材料。

如果仅从 Git 仓库获取源码，根 `LICENSE` 提供了项目 MIT 声明和部分第三方文本，基本许可信息是可见的。如果进行企业私有化交付、发布容器镜像、提供离线包或构建商业衍生产品，应在发布前完成一次基于实际产物的开源软件成分分析，并将许可证、第三方声明、NOTICE、源码获取方式和 SBOM 一并纳入交付物。

## 11. 官方许可证依据

- Open Source Initiative：The MIT License  
  <https://opensource.org/license/mit>
- Apache Software Foundation：Apache License, Version 2.0  
  <https://www.apache.org/licenses/LICENSE-2.0>
- Free Software Foundation：GNU Lesser General Public License v2.1  
  <https://www.gnu.org/licenses/old-licenses/lgpl-2.1.html>
- Eclipse Foundation：Eclipse Public License v2.0  
  <https://www.eclipse.org/legal/epl-2.0/>

