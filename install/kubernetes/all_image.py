import json
import importlib.util
import os,re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
brand_spec = importlib.util.spec_from_file_location('modelone_brand_config', ROOT / 'myapp/brand.py')
brand_module = importlib.util.module_from_spec(brand_spec)
brand_spec.loader.exec_module(brand_module)
snapshot = json.loads((ROOT / 'config/resource-sources.json').read_text())
# 所需要的所有镜像
kubeflow = [
    'mysql:8.0.32',  # 数据库
    'modelone/redis:7.4',  # 缓存
    "busybox:1.36.0",
    "kubeflow/training-operator:v1-8a066f9",  # 分布式训练
    'alpine:3.10',
]

kubernetes_dashboard = [
    'kubernetesui/dashboard:v2.6.1',  # k8s dashboard
    'modelone/k8s-dashboard:v2.6.0',
    'kubernetesui/metrics-scraper:v1.0.8',  # k8s dashboard 上的指标监控
]

new_gpu = [
    'nvidia/k8s-device-plugin:v0.11.0-ubuntu20.04',  # gpu k8s插件
    'nvidia/dcgm-exporter:3.1.7-3.1.4-ubuntu20.04',  # gpu监控
]

new_prometheus = [
    "prom/prometheus:v2.27.1",  # peomethues数据库
    'prom/node-exporter:v1.5.0',  # 机器指标

    'quay.io/prometheus-operator/prometheus-config-reloader:v0.46.0',  # prometheus配置翻译
    "quay.io/prometheus-operator/prometheus-operator:v0.46.0",  # prometheus 部署工具
    'modelone/kube-rbac-proxy:0.14.1',  # 指标
    'carlosedp/addon-resizer:v1.8.4',  # 指标

    'grafana/grafana:9.5.20',  # 监控看板
    "modelone/prometheus-adapter:v0.9.1",  # peometheus指标翻译为自定义指标
]

istio = [
    "istio/proxyv2:1.15.0",  # ingressgateway
    "istio/pilot:1.15.0"  # 数据面
]
volcano = [
    'volcanosh/vc-controller-manager:v1.7.0',  # 控制器
    'volcanosh/vc-scheduler:v1.7.0',  # 调度器
    'volcanosh/vc-webhook-manager:v1.7.0'  # 拦截器
]

pipeline = ['minio/minio:RELEASE.2023-04-20T17-56-55Z'] + [
    row['source'] for row in snapshot['resources']
    if row['kind'] == 'image' and 'cube-argoproj/' in row['source']
]
modelone_images = [
    # 前后端
    'modelone/kubeflow-dashboard-frontend:2026.06.01',
    'modelone/kubeflow-dashboard:2026.06.01',
    # notebook基础镜像
    'modelone/notebook:vscode-ubuntu-cpu-base',
    'modelone/notebook:vscode-ubuntu-gpu-base',
    'modelone/notebook:jupyter-ubuntu22.04',
    'modelone/notebook:jupyter-ubuntu22.04-cuda11.8.0-cudnn8',
    'modelone/notebook:jupyter-ubuntu-cpu-1.0.0',
    'modelone/notebook:jupyter-ubuntu-bigdata',
    'modelone/notebook:jupyter-ubuntu-machinelearning',
    'modelone/notebook:jupyter-ubuntu-deeplearning',
    # 超参搜索的镜像
    'modelone/nni:20250601',
    # 内部服务镜像
    "phpmyadmin:5.2.1",
    # "modelone/patrikx3:latest",
    # "mongo-express:0.54.0",
    # "modelone/neo4j:4.4",
    # "dpage/pgadmin4",
    # "elasticsearch:7.12.1"
    # 推理服务的镜像

    # 'modelone/tfserving:2.14.1-gpu',
    # 'modelone/tfserving:2.14.1',
    # 'modelone/tfserving:2.13.1-gpu',
    # 'modelone/tfserving:2.13.1',
    # 'modelone/tfserving:2.12.2-gpu',
    # 'modelone/tfserving:2.12.2',
    # 'modelone/tfserving:2.11.1-gpu',
    # 'modelone/tfserving:2.11.1',
    # 'modelone/tfserving:2.10.1-gpu',
    # 'modelone/tfserving:2.10.1',
    # 'modelone/tfserving:2.9.3-gpu',
    # 'modelone/tfserving:2.9.3',
    # 'modelone/tfserving:2.8.4-gpu',
    # 'modelone/tfserving:2.8.4',
    # 'modelone/tfserving:2.7.4-gpu',
    # 'modelone/tfserving:2.7.4',
    # 'modelone/tfserving:2.6.5-gpu',
    # 'modelone/tfserving:2.6.5',
    # 'modelone/tfserving:2.5.4-gpu',
    # 'modelone/tfserving:2.5.4',
    'modelone/tfserving:2.3.4',
    # 'modelone/tritonserver:21.12-py3',
    # 'modelone/tritonserver:21.09-py3',
    'modelone/tritonserver:22.07-py3',
    'modelone/torchserve:0.7.1-cpu',
    # 'modelone/torchserve:0.9.0-gpu',
    # 'modelone/torchserve:0.9.0-cpu',
    # 'modelone/torchserve:0.8.2-gpu',
    # 'modelone/torchserve:0.8.2-cpu',
    # 'modelone/torchserve:0.7.1-gpu',
    'modelone/torchserve:0.7.1-cpu'
    # 'modelone/onnxruntime:latest',
    # 'modelone/onnxruntime:latest-cuda',
]

user_image = [
    # 任务模板的镜像
    "ubuntu:20.04",
    'python:3.9',
    'docker:23.0.4',

    # 用户可能使用的基础镜像
    'modelone/ubuntu-gpu:cuda11.8.0-cudnn8-python3.9',

]

# 任务模板的镜像
with (ROOT / 'myapp/init/init-job-template.json').open(encoding='utf-8') as source:
    all_job_templates = json.load(source)
job_template_images = [template['image_name'] for template in list(all_job_templates.values())]

## 示例需要的镜像
example_images=[]
for file in (ROOT / 'myapp/init').iterdir():
    if not file.is_file():
        continue
    content = file.read_text(encoding='utf-8')
    matchs = re.findall(r'(?<![\w/.-])modelone/[a-z0-9][a-z0-9./_-]*(?::[A-Za-z0-9_.-]+)?', content)
    for match in matchs:
        if match not in example_images:
            example_images.append(match.strip())

catalog_registry = Counter(tuple(row['source'].split('/', 2)[:2])
                           for row in snapshot['resources'] if row['kind'] == 'image').most_common(1)[0][0]
catalog_images = ['modelone/' + row['source'].split('/', 2)[2]
                  for row in snapshot['resources']
                  if row['kind'] == 'image' and tuple(row['source'].split('/', 2)[:2]) == catalog_registry]
images = kubeflow + kubernetes_dashboard + new_gpu + new_prometheus + istio + volcano + pipeline + modelone_images + user_image + job_template_images + example_images + catalog_images
images = list(set(images))
init_images = kubeflow + kubernetes_dashboard + new_gpu + new_prometheus + istio + volcano + pipeline



# Generate a reviewable plan. Product images must exist in the enterprise
# registry; image copy and packaging run only when generated scripts are invoked.
import argparse
import sys
sys.path.insert(0, str(ROOT / 'scripts'))
from image_bundle import generate, manifest_images

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate modelOne image transfer scripts without pulling images')
    parser.add_argument('--output', type=Path, default=Path.cwd())
    parser.add_argument('--manifest', type=Path, action='append', default=[], help='include concrete image fields from a rendered deployment; may be repeated')
    parser.add_argument('--manifest-root', type=Path,
                        help='include every YAML manifest below a source root')
    parser.add_argument('--image-list', type=Path, help='additional newline-delimited runtime images')
    args = parser.parse_args()
    try:
        images += manifest_images(args.manifest)
        if args.manifest_root:
            paths = sorted(args.manifest_root.rglob('*.yaml')) + sorted(args.manifest_root.rglob('*.yml'))
            images += manifest_images(paths)
        if args.image_list:
            images += [line.strip() for line in args.image_list.read_text().splitlines() if line.strip()]
        registry = os.environ.get('MODELONE_IMAGE_REGISTRY') or brand_module.BRAND['image_registry']
        generate(images, registry, args.output)
    except ValueError as error:
        parser.error(str(error))
