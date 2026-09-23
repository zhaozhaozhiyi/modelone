> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 镜像

```
pytorch: 
ccr.ccs.tencentyun.com/cube-studio/torchserve:0.5.0-cpu
ccr.ccs.tencentyun.com/cube-studio/torchserve:0.5.0-gpu
ccr.ccs.tencentyun.com/cube-studio/torchserve:0.4.2-cpu
ccr.ccs.tencentyun.com/cube-studio/torchserve:0.4.2-gpu
```
支持的torch版本参考：https://github.com/pytorch/serve/releases
```
torch-server:0.5.1
 - Torch 1.10+ Cuda 10.2, 11.3
 - Torch 1.9.0 + Cuda 11.1
 - Torch 1.8.1 + Cuda 9.2

torch-server:0.4.1
Torch 1.9.0 + Cuda 10.2, 11.1
Torch 1.8.1 + Cuda 9.2, 10.1

torch-server:0.4.0
Cuda 10.1, 10.2, 11.1
```

# 模型导出

**一定要导出完整的模型，包括模型结构和模型参数**


```
# 保存加载模型权重
# torch.save(model.state_dict(), PATH)
# model.load_state_dict(torch.load(PATH))

# 保存完整模型
torch.save(model, PATH)   
model = torch.load(PATH)

model.eval()   # 转为推理模式
example_input = torch.rand(1,3,224,224)
traced_model = torch.jit.trace(model, example_input)   # 序列优化
traced_model.save('./model.pt') # 保存完成模型
```


#  pt模型打包（系统完成）

```
pip3 install torch-model-archiver
cd $model_dir/$model_name
torch-model-archiver --model-name $model_name --version $model_version --handler image_classifier --serialized-file $model_version/$model_name --export-path $model_version -f

其中 --handler 支持如下 image_classifier，image_segmenter，object_detector，text_classifier 

注意：自定义py函数，参考后面
```


# 编写模型配置文件（系统完成）

 `$model_dir/$model_name/config.properties`


```
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
cors_allowed_origin=*
cors_allowed_methods=GET, POST, PUT, OPTIONS
cors_allowed_headers=X-Custom-Header
number_of_netty_threads=32
enable_metrics_api=true
job_queue_size=1000
async_logging=false
```

# 编写日志配置文件（系统完成）

`$model_dir/$model_name/log4j.properties`


```
log4j.logger.ACCESS_LOG = INFO, access_log

log4j.appender.access_log = org.apache.log4j.RollingFileAppender
log4j.appender.access_log.File = ${LOG_LOCATION}/access_log.log
log4j.appender.access_log.MaxFileSize = 100MB
log4j.appender.access_log.MaxBackupIndex = 5
log4j.appender.access_log.layout = org.apache.log4j.PatternLayout
log4j.appender.access_log.layout.ConversionPattern = %d{ISO8601} - %m%n

log4j.logger.com.amazonaws.ml.ts = DEBUG, ts_log

log4j.appender.ts_log = org.apache.log4j.RollingFileAppender
log4j.appender.ts_log.File = ${LOG_LOCATION}/ts_log.log
log4j.appender.ts_log.MaxFileSize = 100MB
log4j.appender.ts_log.MaxBackupIndex = 5
log4j.appender.ts_log.layout = org.apache.log4j.PatternLayout
log4j.appender.ts_log.layout.ConversionPattern = %d{ISO8601} [%-5p] %t %c - %m%n
```

# 部署服务（系统完成）

启动命令：统一填写 


```
启动目录： 留空
启动命令：
torchserve --start --foreground --model-store $model_dir/$model_name/$model_version --models $model_name1=$model_name1.mar --ts-config $model_dir/$model_name/config.properties ---log-config $model_dir/$model_name/log4j.properties
```


# api 访问

```

推理（8080端口）
POST /v1/models/{model_name}:predict      推荐的接口，兼容kfserving
POST /predictions/{model_name}            原生接口
POST /predictions/{model_name}/{version}

健康检查 8080/ping

管理（8081）
GET /models
监控（8082）
POST /metrics


image_classifier接口
# pytorch
SERVER_URL = 'http://resnet50-torchserver.service.kfserving.woa.com/predictions/resnet50'
IMAGE_PATH = 'smallcat.jpg'
files = {'data': open(IMAGE_PATH, 'rb')}
response = requests.post(SERVER_URL, files=files)
print(response.json())
# print(response.content)
print(response.status_code)
response.raise_for_status()

# curl http://resnet50-torchserver.service.kfserving.woa.com/predictions/resnet50 -T smallcat.jpg 
# curl http://resnet50-torchserver.service.kfserving.woa.com/predictions/resnet50 -F "data=@smallcat.jpg"

其他类型接口参考 https://pytorch.org/serve/default_handlers.html
```


# 自定义handler

示例：MNISTDigitClassifier 根据用户输入的图片地址，先下载图片再推理图片，同时返回申请的images_id

生成handler.py文件

```
from torchvision import transforms
from ts.torch_handler.image_classifier import ImageClassifier
import base64,time,json
import torch
from PIL import Image
import io
import requests
import pysnooper

class MNISTDigitClassifier(ImageClassifier):

    image_processing = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize((0.1307,), (0.3081,))
    ])

    # @pysnooper.snoop()
    def handle(self, data, context):
        # 输入输出为list
        start_time = time.time()

        self.context = context
        metrics = self.context.metrics
        data_preprocess = self.preprocess(data)

        if not self._is_explain():
            output = self.inference(data_preprocess)
            output = self.postprocess(output)
        else:
            output = self.explain_handle(data_preprocess, data)

        stop_time = time.time()
        metrics.add_time('HandlerTime', round(
            (stop_time - start_time) * 1000, 2), None, 'ms')
        back=[]
        for index in range(len(output)):
            back.append({
                "predict":output[index],
                "image_id":data[index]['body']['image_id']
            })
        return back


    # @pysnooper.snoop()
    def preprocess(self, data):
        des_images = []
        for row in data:
            image_url=row.get("body")['image_url']
            image = requests.get(image_url).content
            if isinstance(image, (bytearray, bytes)):
                image = Image.open(io.BytesIO(image))
                image = self.image_processing(image)
            else:
                # if the image is a list
                image = torch.FloatTensor(image)

            des_images.append(image)

        return torch.stack(des_images).to(self.device)

    # @pysnooper.snoop()
    def postprocess(self, data):
        return data.argmax(1).tolist()

```
（系统可自动完成）将handler.py加入到mar文件中，将生成的mar文件填入到界面上即可
```
torch-model-archiver --model-name xx --version 1.0 --handler handler.py --serialized-file xx.pt --export-path ./ -f

```
client.py
```
data = {
    "image_url":"http://xx.xx.xx/xx",
    "image_id":"11111"
}
url='http://127.0.0.1:8080/v1/models/mnist:predict'
res = requests.post(url, json=data)
print(res.status_code)
result = res.content.decode()
print(result)
```
