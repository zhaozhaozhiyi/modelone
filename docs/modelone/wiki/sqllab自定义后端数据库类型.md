> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 实现原理
用户提交sql，选定计算引擎，modelOne根据选定的计算引擎和用户提交的sql，发起异步任务，正式的执行在worker中，结果保存在分布式存储csv中

要求: sqllab只能对接查询引擎，通过网络请求，发送sql，并不能作为driver端，无法监听端口。所以无法作为spark的driver端，只能对接clickhouse，presto，imapa等查询网关。

# 计算引擎参数配置
view_sqllab.py中sqllab_config 接口，表征了sqllab界面配配置参数，可以用于配置可用的计算引擎。

# 计算引擎对接

对接计算引擎需要实现对接中的
submit_task 提交sql查询任务
check_task 任务信息查询
get_result 获取任务结果
download_url  获取下载地址
stop 关闭任务几个功能

## 派生方法

派生Base_Impl类，实现具体计算引擎的实现逻辑




