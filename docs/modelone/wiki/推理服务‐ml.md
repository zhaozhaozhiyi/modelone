> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 镜像

```
ccr.ccs.tencentyun.com/cube-studio/ml-server:20231001
```

# 配置config.json

```
[
    {
        "name": "模型英文名",
        "model_path": "模型地址",
        "algorithm": "decisiontree",
        "version": "20231001",
        "enable": true
    },
    {
        "name": "模型英文名",
        "model_path": "模型地址",
        "algorithm": "r",
        "version": "20231001",
        "enable": true
    }
]

```
1、地址支持http/https在线地址
2、xgb模型需要保存为.model格式,r语言的模型需要保存为.pmml,sklearn模型需要保存为.pkl


# 启动命令

```
python server.py --config_path xxx
```

# 标准化模型接口

Model status API：

```
GET http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}|]
示例：
https://demo.service.kfserving.woa.com/v1/models/my_model1/versions/20210924
```

Model Metadata API

```
GET http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}/metadata
示例：
https://demo.service.kfserving.woa.com/v1/models/my_model1/versions/20210924/metadata
```

Predict API

```
POST http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}/predict

示例：

http://xx.xx.xx.xx/v1/models/my_model1/versions/20210924:predict
```