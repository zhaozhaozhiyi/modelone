> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 镜像

```
tensorrt: 
nvcr.io/nvidia/tensorrtserver:19.05-py3
nvcr.io/nvidia/tritonserver:21.09-py3
```

# 目录结构：

**注意：名称必须为model.onnx或者model.plan**

```
<model-repository-path>/
    <model-name>/
      config.pbtxt
      model-version/
       model-file:model.plan/model.onnx
```

# 配置config.pbtxt

注意：不确定填的对不对，可以先不填，系统会自动识别
```
platform: "onnxruntime_onnx"    # tensorrt_plan/pytorch_libtorch/onnxruntime_onnx/tensorflow_savedmodel
name: "resnet50"    
max_batch_size: 0    # 启动动态批处理的话，按情况设定
input [
  {
    name: "your_input_name"
    data_type: TYPE_FP32
    format: FORMAT_NCHW
    dims: [ 3, 224, 224 ]
    reshape { shape: [ 1, 3, 224, 224 ] }
  }
]
output [
  {
    name: "your_output_name"
    data_type: TYPE_FP32
    dims: [ 1000 ]
    reshape { shape: [ 1, 1000 ] }
  }
]
... 其他专门的优化参数
```

# 启动命令


```
tritonserver --model-repository=<model-repository-path> --strict-model-config=false 
```

获取自动生成配置

```
curl localhost:8000/v2/models/<模型名称>/config
```

# api访问

建议使用tirton提供的客户端包。

```
pip3 install tritonclient[all]
pip3 install attrdict  
```

# 标准化模型接口

tfserving、torchserver、onnxruntime、tensorrt
```
/v1/model/$model_name
/v1/model/$model_name/version/$version_name
/v2/health/ready  健康检查
```

# onnx模型推理加速

## tf/pytorch转onnx模型

pytorch模型转onnx模型

```
model.eval()     # 设置模型为推理模式
dummy_input = torch.randn(1, 3, 224, 224)  # 输入样本
export_onnx_file = "resnet50.onnx"         # 目的ONNX文件名
torch.onnx.export(
    model,dummy_input,export_onnx_file,
    opset_version=13,           # 转为onnx的版本
    do_constant_folding=True,   # 是否执行常量折叠优化
    input_names=["input_name"],     # 输入名
    output_names=["output_name"],   # 输出名
    # dynamic_axes={
    #     "input":{0:"batch_size"},   # 批处理变量
    #     "output":{0:"batch_size"}
    # },
    dynamic_axes={'input_name': [2, 3], 'output_name': [2, 3]}   # 动态size的输入输出的维度
)
```
tf模型转onnx模型
```
# pip install tensorflow-onnx tf2onnx
python -m tf2onnx.convert --saved-model ./saved_model  --output ./live_deepfm_low.onnx --opset 13
```
## 模型配置

在线查看模型结构：https://netron.app/

按照模型结构填写配置即可，主要是input和output信息

# pytorch 模型加速

pytorch 模型加速，需要选择**方法4**保存TORCHSCRIPT模型
```

# # 方法1、保存完成的模型
# torch.save(model,'mnist.pt')
#
# # 方法2：保存网络参数
# PATH = './cifar_net.pth'
# torch.save(model.state_dict(), PATH)
#
# # 方法3：导出网络到ONNX
# dummy_input = torch.randn(1,1,28, 28).to(device)
# torch.onnx.export(model, dummy_input, "torch.onnx")

# 方法4：保存TORCHSCRIPT
# dummy_input = torch.randn(1,1,28, 28).to(device)
# traced_cell = torch.jit.trace(model, dummy_input)
# traced_cell.save("torchscript.pt")

```
## 模型配置

torch script保存的模型，目前不提供输入和输出的端口的命名，因此在配置文件中，输入和输出端口的名字必须按照如下命名： `"INPUT__0", "INPUT__1" and "OUTPUT__0", "OUTPUT__1"`

