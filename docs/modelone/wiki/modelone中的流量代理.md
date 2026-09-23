> **状态：上游继承，modelOne 待核验。** 本页内容来自 CubeStudio Wiki 上游版本，尚未逐项对照 modelOne 当前代码和部署配置。文中的旧项目名称、仓库路径、镜像、域名、示例数据、截图及外部资源均须在使用前核验；可用的当前说明请先查阅 [modelOne 交付文档](../README.md) 和[迁移记录](MIGRATION.md)。


# 流量入口

istio-system命名空间，istio-ingressgateway，80端口

# 流量代理

| 路径 |命名空间 | 服务 |
|----|----|----|
| /   |  infra  | 先代理到kubeflow-dashboard-frontend，再代理到kubeflow-dashboard后端pod|
| /frontend/   |  infra  | kubeflow-dashboard-frontend前端pod |
| /grafana/  | prometheus | grafana|
| /gradio/aihub/$name | aihub | aihub应用 |
| /aihub/$name | aihub | aihub应用 |
| /notebook/jupyter/$name | jupyter | notebook应用 |
| /k8s/dashboard/cluster/ | kube-system | 高权限 k8s dashboard |
| /k8s/dashboard/user1/ | kube-system | 低权限 k8s dashboard |
| /labelstudio/ | kubeflow | labelstudio标注平台 |
