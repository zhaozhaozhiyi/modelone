> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。

# 一、sqllab简介

sqllab是用来对接各类型数据库的，可以实现在计算平台中查询数据库中的数据，避免计算平台和数据库中来回切换。

# 二、sqllab使用

## 1. 连接数据库

sqllab中可以连接的数据库包括mysql、postgresql等。选择好数据库类型后，按照规定的格式填写登录数据库的用户名、密码、端口等信息。

## 2. 查询数据库

在sqllab窗口中填写需要查询的语句，点击运行即可。需要注意的是，目前sqllab仅支持select语句，且必须加上limit。查询的结果可以在线查看，也可以下载。

![](https://foruda.gitee.com/images/1698378204862496999/c9dd9cb4_1019082.png)

mysql查询示例：

sql：

`select * from ab_user limit 1;`

数据库：

`mysql+pymysql://root:admin@mysql-service.infra:3306/kubeflow`

#### postgresql查询示例：

sql: 

`select * from ml_mlbackend limit 1;`

数据库：

`postgresql+psycopg2://postgres:postgres@postgresql.kubeflow:5432/labelstudio`

在线查看查询结果如图所示

![输入图片说明](https://foruda.gitee.com/images/1698378827234990067/6359d2eb_1019082.png "屏幕截图")

## 3. 可能出现的错误

如果子任务运行显示fail，首先要考虑数据库的账号、密码等是否正确，其次是所写的查询语句是否支持，是否正确，是否加limit。