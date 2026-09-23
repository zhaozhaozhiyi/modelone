> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 保存saved_model模型添加服务化签名

tf.keras.Model 会自动指定服务上线签名

tf.saved_model.save要手动指定

```
module_with_signature_path = '/xx/'
call = module.__call__.get_concrete_function(tf.TensorSpec(None, tf.float32)) # 第一个参数也可以加上shape，例如(1,256,32,1)
tf.saved_model.save(module, module_with_signature_path, signatures=call)
```

# 查看网络模型结构
pip3 install tensorflow==x.x.x

saved_model_cli show  --all --dir=model_Path

可以看到输入签名
```
signature_def['serving_default']:
  The given SavedModel SignatureDef contains the following input(s):
    inputs['a_age'] tensor_info:
        dtype: DT_INT64
        shape: (-1, 1)
        name: serving_default_a_age:0
		...
  Method name is: tensorflow/serving/predict
```

# tfserving云原生服务部署

## 镜像

```
tensorflow:
tensorflow/serving:1.11.0
tensorflow/serving:1.11.0-gpu
tensorflow/serving:1.12.0
tensorflow/serving:1.12.0-gpu
tensorflow/serving:1.13.0
tensorflow/serving:1.13.0-gpu
tensorflow/serving:1.14.0
tensorflow/serving:1.14.0-gpu
tensorflow/serving:2.0.0
tensorflow/serving:2.0.0-gpu
tensorflow/serving:2.1.4
tensorflow/serving:2.1.4-gpu
tensorflow/serving:2.2.3
tensorflow/serving:2.2.3-gpu
tensorflow/serving:2.3.4
tensorflow/serving:2.3.4-gpu
tensorflow/serving:2.4.3
tensorflow/serving:2.4.3-gpu
tensorflow/serving:2.5.2
tensorflow/serving:2.5.2-gpu
tensorflow/serving:2.6.0
tensorflow/serving:2.6.0-gpu
```

## 模型文件目录结构

`$model_dir/$model_name/$model_version/saved_model.pb`

如下图所示：
         
![image](https://cube-studio.oss-cn-hangzhou.aliyuncs.com/docs/csdn_image/a216aa406301289ed5d56ef6b1d5958c.png)
        

[官网样例](https://github.com/tensorflow/serving/tree/master/tensorflow_serving/servables/tensorflow/testdata/saved_model_half_plus_two_cpu)

## 编写模型配置文件（必须）

`$model_dir/$model_name/models.config`

简单样式：(标准的utf-8编码的json文件)


```
model_config_list {
  config {
    name: "$model_name"
    base_path: "$model_dir/$model_name/"
    model_platform: "tensorflow"
    model_version_policy {
        specific {
           versions: $version
        }
    }
  }
}
```

替换自己的`$model_dir、$model_name和$version`

注意：

1、model_version_policy 设置提供服务的版本，不设置则自动选择最新的模型版本。

2、`$version`只能用int64来命名。

建议放在个人目录某个子目录下，配置服务时用启动命令的 `--model_config_file=$model_dir/$model_name/models.config`  参数指定models.config的路径。


[其他配置文件可选参数](https://www.tensorflow.org/tfx/serving/serving_config)： 

## 编写监控配置文件（必须）

 `$model_dir/$model_name/monitoring.config`
监控配置：


```
prometheus_config {
  enable: true,
  path: "/metrics"
}
```

放在同目录下，配置服务时用启动命令的 

`--monitoring_config_file=$model_dir/$model_name/monitoring.config`

## 编写平台配置文件（可忽略）

`$model_dir/$model_name/platform.config`


```
platform_configs {
  key: "tensorflow"
  value {
    source_adapter_config {
      [type.googleapis.com/tensorflow.serving.SavedModelBundleSourceAdapterConfig] {
        legacy_config {
          session_config {
            gpu_options {
              allow_growth: true
            }
          }
        }
      }
    }
  }
}
```

放在同目录下，配置服务时用启动命令的 

`--platform_config_file=$model_dir/$model_name/platform.config`

## 部署服务

        
启动命令：统一填写 `/usr/bin/tf_serving_entrypoint.sh --model_config_file=xxx`，必须指定部署配置文件的路径 `--model_config_file`。

后面可选添加其他配置项，常用如监听端口、服务线程数、配置更新间隔、启用缓存、证书鉴权等，详见


```
--model_config_file        模型配置文件
--monitoring_config_file          监控配置文件
--enable_batching   是否启动批处理
--batching_parameters_file     批处理配置文件
--platform_config_file      平台配置文件

--port           监听 gRPC API 的端口
--rest_api_port           监听 HTTP/REST API 的端口
--rest_api_num_threads=64      # 并发线程数，会默认配置
--rest_api_timeout_in_ms           HTTP/REST API 调用超时
--file_system_poll_wait_seconds     服务器轮询文件系统以获取每个模型各自model_base_path 处的新模型版本的时间段
--enable_model_warmup        使用 assets.extra/ 目录中用户提供的 PredictionLogs启用模型预热
--tensorflow_intra_op_parallelism=10    建议设置为申请的cpu核数目
--tensorflow_inter_op_parallelism=10    建议设置为申请的cpu核数目
```


日志跟踪


```
TF_CPP_MIN_VLOG_LEVEL=1    详细日志
TF_CPP_VMODULE=http_server=1    api请求日志
```

支持的启动参数：https://github.com/tensorflow/serving/blob/master/tensorflow_serving/model_servers/main.cc#L59 

内存申请，cpu申请，gpu申请：按需申请。

域名：按具体业务填写

镜像：选取合适版本镜像

端口：8501

# tfserving api访问

官方文档：https://github.com/tensorflow/serving/blob/master/tensorflow_serving/g3doc/api_rest.md 

Model status API：

```
GET http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}|/labels/${LABEL}]
示例：
https://demo.service.kfserving.woa.com/v1/models/my_model1/versions/20210924
```

Model Metadata API

```
GET http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}|/labels/${LABEL}]/metadata
示例：
https://demo.service.kfserving.woa.com/v1/models/my_model1/versions/20210924/metadata
```

Classify and Regress API

```
POST http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}:(classify|regress)
```

Predict API

```
POST http://host:port/v1/models/${MODEL_NAME}[/versions/${VERSION}|/labels/${LABEL}]:predict

示例：

http://xx.xx.xx.xx/v1/models/my_model1/versions/20210924:predict
```

# 生产中建议不使用版本，这样能做到无缝切换，版本

http://xx.xx.xx.xx/v1/models/my_model1:predict

shell 示例：

`curl -d '{"instances": [1.0, 2.0, 5.0]}' -X POST http://xx.xx.xx/v1/models/my_model1/versions/20210924:predict`

python示例json：
```
req_json = {
    "instances":[
        {
            'input_name1':xx,
            'input_name2':xx,
            ...
        }
    ]
}
predict_request = json.dumps(req_json)
response = requests.post(SERVER_URL, data=predict_request)
response.raise_for_status()
print(response.json())
```

python推理图片：
```
jpeg_rgb = Image.open(io.BytesIO(open(IMAGE_PATH,"rb").read()))
jpeg_rgb = np.expand_dims(np.array(jpeg_rgb) / 255.0, 0).tolist()
predict_request = json.dumps({'instances': jpeg_rgb})
response = requests.post(SERVER_URL, data=predict_request)
response.raise_for_status()
print(response.json())
```