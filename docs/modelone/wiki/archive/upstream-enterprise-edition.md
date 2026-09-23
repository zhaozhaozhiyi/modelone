# 提示：

产品特性：
 - 1，国内开源mlops第一名，上千家企业私有化部署，功能稳定和完善。
 - 2、功能完善，支持sso登录，notebook在线开发，拖拉拽任务流pipeline编排，多机多卡分布式算法训练，超参搜索，推理服务VGPU，多集群调度， 私有化部署/边缘集群/serverless集群，标注平台自动化标注，大模型一键微调，私有知识库，AI应用商店，支持模型一键 开发/推理/微调，支持国产cpu/gpu/npu芯片，支持RDMA。
 - 3，扩展性好，适合机器学习/深度学习/大模型各领域落地。特定算法适配不需要改造平台，企业落地适配性好。
 - 4，支持源码交付，授权可以改造，加工成自己的产品，没有license部署个数和时长限制，可对外出售。
 - 5，支持免费新增功能升级，保持平台先进性
 - 6，仅对企业版特有功能收费，性价比高，同时支持只采购部分功能控制成本。
 - 7，采购前可帮助免费更换logo为客户做演示。

#### 注意： 企业版功能持续更新，建议联系管理员获取企业版最新信息 

# 功能清单

| 模块分组 | 功能 | 功能描述(下划线为企业版本特有) |
| --- | --- | --- |
| 用户权限 | SSO单点登录 | <li>账号密码注册自动登录<li><u>支持对接公司账号体系AUTH_OID/AUTH_LDAP/AUTH_REMOTE_USER等登录注册方式，支持消息推送</u></li><br><li><u>增加登录验证，强密码，远程用户，登录频率限制，密码密文传输显示等</u></li> |
| 用户权限 | 项目组管理 | <li>AI平台需要通过项目划分，支持配置相应项目组用户的权限，任务/服务的挂载，资源组，集群，服务代理，项目组内角色控制，<u>支持用户和项目组删除，支持为项目组指定命名空间，项目组支持绑定多个资源组，支持设置组内用户可用资源组</u></li> |
| 用户权限 | 用户管理<br>角色管理/权限管理 | <li>管理平台用户的基本信息，组织架构，支持账号密码，rbac权限体系</li><br><li><u>增加修改和删除，清理等操作的历史记录，支持菜单权限控制</u></li><br><li><u>支持只读者public角色，支持控制角色可访问接口，以及接口访问类型</u></li><br><li><u>支持多租户(多个用户公司)</u></li> |
| 算力调度 | 数据大屏 | <li>支持全局，项目组，个人级别的任务pod的分布情况</li> |
| 算力调度 | 多资源组/多集群 | <li>支持划分多资源组，支持docker运行时，<u>支持多k8s集群，支持ipvs网络模式，支持containerd容器运行态，支持边缘集群模式</u></li> |
| 算力调度 | gpu调度能力 | <li>提供多种规格的资源支持不同的使用场景，cpu/gpu等 支持T4/V100/A100等多种卡型</li><br><li><u>支持gpu禁用模型，共享模式，独占模式，vgpu模式，支持虚拟化占用显存设定，英伟达支持指定卡序号，支持gpu调度binpack调度策略，支持ib/roce的rdma协议</u></li> |
| 算力调度 | 支持多种算力 | <li><u>平台底层外部组件支持arm架构，前后端镜像支持arm架构，任务模板支持arm架构，notebook镜像支持arm架构，超参搜索支持arm架构，aihub应用70%支持arm架构</u></li><br><li><u>支持调度海光dcu，华为npu算力，壁仞，沐曦、寒武纪、摩尔线程，百度昆仑芯</u></li> |
| 算力调度 | 算力市场 | <li><u>支持算力市场机器空闲状态查看，支持按需占用，和包月包日模式租赁</u></li> |
| 算力调度 | 租赁实例 | <li><u>支持租赁启动pod实例管理，开关机释放等，支持查看当前租赁信息和使用费用ssh登录信息等</u></li><br><li><u>支持包月账单的管理</u></li> |
| 算力调度 | 计量计费功能 | <li><u>1、支持平台资源限制的分配和查看</u></li><br><li><u>项目组资源限制，用户资源限制、任务资源限制，项目组下个人的资源限制，包括开发资源，训练资源、推理资源等</u></li><br><li><u>额度限制限制在notebook，docker构建，pipeline，超参搜索，内部服务，推理服务中的生效</u></li><br><li><u>限制支持单任务，并行任务总和和历史任务总和等方法</u></li><br><li><u>2、提供统一的开发、训练、推理服务资源监控，从用户、项目、任务角度分析模型资源分配及使用情况</u></li><br><li><u>3、支持自定义计费模式，通过计量结果自定义获取计费值</u></li><br><li><u>4、按需占用日结账单，产生用户每日账单费用和明细</u></li> |
| 算力调度 | 机器资源管理 | <li><u>web界面控制机器调度类型，所属资源组，是否启动rdma，是否启动vgpu，可用任务场景等</u></li> |
| 算力调度 | 存储盘管理 | <li><u>支持web界面添加存储盘，支持项目组绑定，notebook pipeline 推理服务，直接在pod中挂载外部分布式存储</u></li><br><li><u>支持nfs，cfs，oss，nas，cos，glusterfs，cephfs，s3/minio</u></li> |
| 基础能力 | 网络 | <li>支持80、非80端口，支持公网/域名<u>，支持反向代理和内网穿透方式访问，支持https</u></li> |
| 基础能力 | 数据库存储 | <li><u>支持外部</u>mysql<u>/postgres/OceanBase/人大金仓/达梦作为元数据库(不含标注模块)</u></li> |
| 基础能力 | 国际化能力 | <li><u>mlops支持配置多语言配置，目前支持8国语言翻译</u></li> |
| 数据管理 | 数据地图 | <li>元数据库表管理，指标，维表</li> |
| 数据管理 | 数据计算 | <li>sqllab交互查询，支持mysql，<u>postgresql，clickhouse，hive，presto，达梦数据库</u>等计算引擎，<u>支持数据分析建模</u></li> |
| 数据管理 | 数据集管理 | <li>允许用户随时上传样本集（图片、音频、文本等），<u>对表格数据支持数据集一键探索功能</u></li> |
| 数据标注 | 数据标注 | <li><u>支持图/文/音/多模态各类型标注能力</u></li><br><li><u>支持分布式存储打通mlops平台</u></li><br><li><u>支持项目组权限控制，支持普通用户标注草稿，审核员核定，标注质量打分，导入导出批量删除设置等区分角色的权限控制</u></li><br><li><u>标注任务分配</u></li><br><li><u>目前支持8国语言翻译</u></li><br><li><u>labelstudio标注数据导入pipeline</u></li><br><li><u>支持从数据集模块导入和导出到数据集模块</u></li><br><li><u>支持pg/人大金仓数据库</u></li><br><li><u>支持项目状态管理和webhook</u></li> |
| 数据标注 | 数据标注 | <li><u>支持自动化标注：支持目标识别，目标边界识别，目标遮罩识别，图片分类，图片描述，ocr，支持图片转markdown，关键点检测，视频多目标跟踪，多说话人语音分隔，语音识别，结构化数据标注</u></li><br><li><u>支持视觉大模型自动化标注：支持目标识别万物识别，支持目标边界检测万物分隔，支持目标遮罩万物分隔</u></li><br><li><u>支持大模型自动化标注：文本分类，文本翻译，命名实体识别，阅读理解，问答，摘要提取，答案排序</u></li> |
| 在线开发 | 镜像功能 | <li>镜像仓库/镜像管理/在线构建镜像</li><br><li>同时提供平台所有镜像，包括模板镜像/服务镜像/notebook镜像/gpu基础环境的构建方法和构建后镜像，</li><br><li><u>支持同一仓库多个秘钥配置，支持在线镜像构建</u></li> |
| 在线开发 | notebook | <li>支持基于开源的Jupyterlab/vscode<u>汉化版</u>，提供在线的交互式开发调试工具</li><br><li>提供多种可选环境ide和开发示例，支持资源类型选择</li><br><li>支持大数据版本，机器学习版本，深度学习版本</li><br><li><u>大数据版本支持用户信息，hdfs客户端，hive客户端和spark客户端</u></li><br><li>支持ssh remote与notebook对接远程开发，方便快速将本地代码提交到平台的训练环境</li><br><li><u>ssh jumpproxy，单端口开放</u></li><br><li><u>支持gpu，cpu，内存，监控，支持git交互</u></li><br><li><u>支持自定义notebook镜像，便于封装公司自己的notebook</u></li><br><li><u>多环境notebook，支持R语言/julia语言/python2.7/python3.6/python3.7/python3.8/python3.9/python3.10环境和cube-studio专有环境</u></li><br><li><u>在线ide支持claude code对接内网或国内模型</u></li><br><li><u>支持tensorboard任务可视化</u></li><br><li><u>notebook支持环境镜像保存</u></li><br><li><u>jupyter支持密码保护</u></li><br><li><u>notebook支持整卡占用，虚拟卡占用，gpu共享占用</u></li><br><li><u>notebook支持指定调度机器</u></li><br><li><u>支持华为npu算力的在线jupyter开发</u></li><br><li><u>支持海光dcu算力的在线jupyter开发</u></li><br><li><u>支持沐曦算力的在线jupyter开发</u></li><br><li>支持notebook启动自动初始化</li><br><li>支持notebook自动清理，续期</li> |
| 模型训练 | 拖拉拽任务流编排调试 | <li>提供拖拽式交互开发环境，支持开发者以拖拽的方式完成业务逻辑的PIPLINE</li><br><li>支持单任务调试，训练支持多种资源规格（CPU、GPU等），支持卡型的选择，超时重试等，任务支持独占<u>和共享占用gpu</u></li><br><li>分布式任务模板支持单任务调试用户镜像而非模板镜像</li><br><li><u>支持rdma资源占用</u></li><br><li><u>支持gpu不同厂商，不同卡型的占用</u></li><br><li><u>分布式任务模板支持gpu型号透传，rdma资源透传，拉取秘钥透传</u></li><br><li>pipeline调试，<u>支持定时调度，补录，并发限制，超时，实例依赖等</u>，任务管理，workflow实例管理，资源监控，<u>支持任务输入输出，任务流全局常量，文本/图片/csv/json/表格/echart结果可视化，支持workflow暂停和恢复</u></li><br><li><u>支持单任务和pipeline运行中任务监听端口提供运行中服务监听能力</u></li><br><li><u>定时调度支持最大保留实例数</u></li><br><li><u>pipeline支持任务流优先级</u></li> |
| 模型训练 | 主流功能算子 | <li>基础算子：自定义镜像，<u>逻辑节点，python</u></li><br><li>数据同步：数据集导入(<u>支持huggingface/魔塔数据集</u>)，datax，<u>datax-import</u>，模型导入(<u>支持huggingface/魔塔模型</u>)，<u>datax-import支持mysql,postgresql,clickhouse</u></li> |
| 模型训练 | 主流功能算子 | <li><u>特征处理：</u></li><br><li><u>-数据合并，包含union、join操作</u></li><br><li><u>-去除重复样本</u></li><br><li><u>-数据变换，包括boxcox转换、二值化、数据类型转换、dct变换、根据函数转换、ma移动平均、多项式展开</u></li><br><li><u>-非数值型变量处理，包括hash、根据统计量转换、one-hot</u></li><br><li><u>-异常值检测</u></li><br><li><u>-获取变量的统计量</u></li><br><li><u>-去除值过于单一的变量</u></li><br><li><u>-删除缺失率过高的值</u></li><br><li><u>-删除缺失率过高的值</u></li><br><li><u>-填充缺失值</u></li><br><li><u>-数据离散化，等宽、等频、聚类离散化</u></li><br><li><u>-标准化、正则化、归一化，有最大绝对值归一化、最大最小归一化、z_score标准化</u></li><br><li><u>-索引处理，包含增加索引、索引转列、列索引重命名</u></li><br><li><u>-排序</u></li><br><li><u>-执行sql</u></li><br><li><u>-hadamard乘积</u></li><br><li><u>-特征组合，用于衍生特征</u></li><br><li><u>-降维，包括pca降维和卡方降维</u></li><br><li><u>-特征重要性，通过随机森林、逻辑回归、xgboost等模型计算特征重要性，可计算特征的iv值、互信息值、方差等</u></li><br><li><u>-特征向量间的相关性计算</u></li><br><li><u>-数据拆分，包括列内拆分、列间拆分、行间拆分、svd奇异值分解</u></li><br><li><u>-采样，包括随机采样、分层采样、过采样、欠采样</u></li> |
| 模型训练 | 主流功能算子 | <li>数据处理工具：volcanojob/ray分布式数据处理，<u>hadoop模板支持hadfs，hive命令，spark命令</u></li><br><li>文本数据处理：</li><br><li><u>paddleocr-vl pdf/doc/图片等提取为markdown，markdown提取问答对，问答扩展，清理异常数据，过滤数据，替换隐私数据，文本数据统计</u></li><br><li>图像数据处理：</li><br><li><u>图片质量评估、图片去噪声，图片缩放，图片标准化，图片裁剪，图片均衡化，图片的空间转换，图片变换(旋转，平移，缩放，翻转</u></li><br><li>视频处理：分布式媒体下载，视频提取图片，视频提取图片</li> |
| 模型训练 | 主流功能算子 | <li>传统机器学习：sklearn单机，<u>ray-sklearn分布式</u>，xgb单机训练推理</li><br><li>传统机器学习算法：<u>ar/arima时间序列算法/random-forest/random-forest-regression/lr/lightgbm/knn/kmean/gbdt/decision-tree//pca/lda/catboost/xgb，超参搜索</u></li> |
| 模型训练 | 主流功能算子 | <li>分布式深度学习框架：tf/pytorch</li> |
| 模型训练 | 主流功能算子 | <li><u>模型处理：模型评估，模型格式转换</u></li><br><li>模型服务化：模型注册，模型离线处理，模型部署</li> |
| 模型训练 | 算子自定义 | <li>支持算子自定义，通过web界面操作将自定义算法代码镜像，注册为可被他人复用的pipeline算子，<u>自定义任务模板额外支持int型，float型，list型，bool型，json型，子类型支持workdir类型，image类型，select-input，select2，project类型，支持参数tip提醒</u></li> |
| 模型训练 | 链路共享 | <li>面向非AI背景的用户提供自动学习服务，用户选择某一个场景之后，上传训练数据即可自动开始训练和模型部署，<u>支持示例pipeline任务流导入导出</u></li> |
| 模型训练 | 自定义镜像 | <li>面向高级 AI 开发者，提供自定义训练作业（执行环境 + 代码）功能</li> |
| 模型训练 | 自动调参 | <li><u>基于单机/分布式自动超参搜索</u></li> |
| 模型训练 | TensorBoard作业 | <li><u>实时/离线观察模型训练过程中的参数和指标变化情况</u></li> |
| 模型管理<br>推理服务 | 内部服务 | <li>支持开发或运维工具快捷部署，提供mysql-web，postgresql web，mobgo web， redis web，neo4j，rstudio等开源工具，<u>支持ollama，xinference大模型推理</u></li> |
| 模型管理<br>推理服务 | 模型管理 | <li>模型管理用于对模型多版本管理，支持模型发布为推理服务，<u>支持模型指标可视化</u></li> |
| 模型管理<br>推理服务 | 推理服务 | <li>支持<u>ml</u>/tf/pytorch/tentortrt/onnx常规模型的多版本的0代码发布</li><br><li>支持gpu卡型选择，<u>支持vgpu，独占，共享占用，</u>支持cpu/mem/<u>gpu等弹性伸缩</u>，<u>支持服务优先级，支持随机分流和header分流，限流，流量复制，sidecar配置</u>，支持泛域名配置，支持配置文件挂载，启动目录/命令/环境变量/端口/指标/健康检查等</li><br><li>支持调试环境/生产环境</li><br><li>支持<u>域名</u>/ip代理多种形式</li><br><li>支持服务负载指标监控</li><br><li><u>支持多版本服务滚动升级和回滚</u></li><br><li><u>支持远程模型路径</u></li><br><li>提供ml/tf/pytorch/tentortrt/onnx常规模型推理服务镜像</li><br><li>支持用户自定义模型推理镜像</li><br><li><u>支持定时伸缩容</u></li><br><li><u>支持配置服务的jwt认证功能</u></li><br><li><u>支持推理服务在线测试</u></li> |
| 监控 | 整体资源 | <li>所有集群，所有计算机器的使用情况，包括机器的所属集群，所属资源组，机器ip，cpu/gpu类型和卡型，当前cpu/内存/gpu的使用率</li><br><li>所有集群，所有计算pod的使用情况，包括pod所属集群，所属资源组，所属命名空间，调度ip，pod名称，启动用户，cpu，gpu，内存的申请使用率</li><br><li><u>整体资源页面，支持管理员批量删除</u></li> |
| 监控 | 监控体系 | <li>所有机器的gpu资源的使用情况，</li><br><li>所有机器的内存/cpu/网络io/磁盘io的负载情况，</li><br><li>所有pod的内存/cpu/gpu/网络io负载情况</li><br><li>所有推理服务的内存/cpu/gpu/qps/吞吐/<u>vgpu负载情况</u></li><br><li><u>支持ib流量监控</u></li><br><li><u>支持首页消息提醒，支持企业微信，钉钉，飞书群聊消息推送</u></li><br><li><u>消息报警记录，统一webhook接口</u></li><br><li><u>npu监控</u></li> |
| AIHUB | 应用sdk | <li><u>提供CubeStudio sdk，提供模型开发规范和使用规范</u></li> |
| AIHUB | 应用sdk | <li><u>提供web端模型应用体验，支持api推理</u></li> |
| AIHUB | 应用sdk | <li><u>提供开发多个python cuda版本的基础镜像</u></li> |
| AIHUB | 预训练模型 | <li><u>提供视觉，听觉，nlp，多模态等400+预训练模型，提供预训练模型的模型加载和推理能力，可直接一键部署服务，并提供api</u></li> |
| AIHUB | 模型市场 | <li><u>aihub应用对接CubeStudio平台进行卡片式展示</u></li> |
| AIHUB | 模型一键开发 | <li><u>提供一键转notebook开发，提供符合当前模型所需环境的jupyter</u></li> |
| AIHUB | 模型一键微调 | <li><u>支持一键转pipeline微调链路，包括示例数据集下载，微调，模型注册，模型部署，支持微调后模型部署</u></li> |
| AIHUB | 模型一键部署web | <li><u>提供模型一键部署提供手机端和pc端web界面和api，和demo示例弹窗演示，支持部署成推理服务</u></li> |
| AIHUB | 模型自动化标注 | <li><u>支持部署对接labelstudio自动化标注</u></li> |
| AIHUB | pipeline对接aihub | <li><u>aihub注册算子，可以将代码目录注册成aihub市场应用</u></li><br><li><u>aihub调用算子，可以调用aihub的应用 做数据处理</u></li> |
| 大模型 | 大模型分布式多机多卡 | <li><u>分布式多机多卡训练和加速框架：mpi/colossalai/deepspeed/horovod/megatron/mindformer/mxnet/paddlejob/mindspore分布式训练</u></li> |
| 大模型 | 支持大模型推理aihub形式 | <li><u>(需购买aihub)：支持openjourney/gpt3/yuan/sd-v2/sd-v1.5/Stable Cascade/Stable Diffusion XL/部署</u></li> |
| 大模型 | 支持大模型推理 | <li><u>支持vllm大模型推理，支持推理加速+流式openai接口</u></li><br><li><u>支持分布式多机多卡vllm大模型推理</u></li><br><li><u>deepseek，qwen2，chatglm4等模型推理示例</u></li><br><li><u>支持llm大模型服务对话测试</u></li><br><li><u>支持mindie昇腾大模型推理服务 支持 910b和310p算力</u></li><br><li><u>支持mindie分布式推理</u></li><br><li><u>支持昇腾/海光/沐曦/寒武纪/摩尔线程/昆仑芯适配的大模型推理</u></li><br><li><u>支持大模型网关，支持统一入口，秘钥设定，qps/tps限速，黑白名单，token限额，有效期设定，多类型秘钥认证，重试，提示词模板，参数值映射，参数值固化，</u></li><br><li><u>流量监控：qps、失败率/tps/输入token量/输出token量/e2e/ttft/tpos指标监控</u></li> |
| 大模型 | 支持大模型微调 | <li><u>支持deepseek/chatglm4/qwen2/llama3 lora微调, mindformers微调模型，支持llama-factory 大模型sft/奖励模型/强化学习，支持npu适配的llama-factory，支持dcu适配llama-factory，支持沐曦适配llama-factory</u></li> |
| 大模型 | 支持大模型量化评估剪枝 | <li><u>支持大模型量化功能，支持llamafactory大模型评估，支持opencompass大模型评估，支持大模型剪枝</u></li> |
| 大模型 | 智能对话 | <li><u>提供支持多场景对话，支持责任人权限，提示词模板构建，推理接口配置，llm问答，tips等设置</u></li> |
| 大模型 | 智能对话 | <li><u>支持清空，修改问题，删除问答对，答案重试，反馈，上传图片多模态问答，切换模型，修改系统提示词，用户提示词模板，修改对话超参数、多窗口对话等，支持问答复制，代码答案下载</u></li><br><li><u>支持展示检索知识库记录</u></li><br><li><u>支持安全问答检测</u></li> |
| 大模型 | 智能对话 | <li><u>支持aihub应用接口模式</u></li> |