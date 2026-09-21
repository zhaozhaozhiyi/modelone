#!/bin/bash
: "${MODELONE_ASSET_BASE_URL:?Set the enterprise resource base URL}"

source "$(dirname "${BASH_SOURCE[0]}")/modelone-manifests.sh" || exit 1
cd "$MODELONE_SOURCE_ROOT" || exit 1

bash init_node.sh
mkdir -p ~/.kube /etc/kubernetes/ && rm -rf ~/.kube/config /etc/kubernetes/admin.conf && cp config ~/.kube/config && cp ~/.kube/config /etc/kubernetes/admin.conf
mkdir -p kubeconfig && echo "" > kubeconfig/dev-kubeconfig

ARCH=$(uname -m)

wget ${MODELONE_ASSET_BASE_URL%/}/install/kubectl && chmod +x kubectl  && cp kubectl /usr/bin/ && mv kubectl /usr/local/bin/

version=`kubectl version --short | awk '/Server Version:/ {print $3}'`
echo "kubernets versison" $version

node=`kubectl  get node -o wide |grep $1 |awk '{print $1}'| head -n 1`
kubectl label node $node train=true cpu=true notebook=true service=true org=public istio=true kubeflow=true kubeflow-dashboard=true mysql=true redis=true monitoring=true logging=true --overwrite

# 创建命名空间
sh create_ns_secret.sh
kubectl apply -f sa-rbac.yaml
# 部署dashboard
kubectl apply -f dashboard/v2.6.1-cluster.yaml
kubectl apply -f dashboard/v2.6.1-user.yaml
# 部署mysql
kubectl create -f mysql/pv-pvc-hostpath.yaml
kubectl create -f mysql/service.yaml
kubectl create -f mysql/configmap-mysql.yaml
kubectl create -f mysql/deploy.yaml
# 部署redis
kubectl delete -f redis/redis.yaml
kubectl create -f redis/redis.yaml

# 部署prometheus
cd prometheus

kubectl apply -f ./grafana/pv-pvc-hostpath.yml
kubectl apply -f ./grafana/grafana-sa.yml
kubectl apply -f ./grafana/grafana-source.yml
kubectl apply -f ./grafana/grafana-datasources.yml
kubectl apply -f ./grafana/grafana-admin-secret.yml
kubectl apply -f ./grafana/grafana-svc.yml
kubectl delete configmap grafana-config all-grafana-dashboards --namespace=monitoring
kubectl create configmap grafana-config --from-file=./grafana/grafana.ini --namespace=monitoring
kubectl create configmap all-grafana-dashboards --from-file=./grafana/dashboard --namespace=monitoring
kubectl delete -f ./grafana/grafana-dp.yml
sleep 5
kubectl apply -f ./grafana/grafana-dp.yml

# 部署prometheus_adapter
kubectl apply -f ./prometheus_adapter/metric_rule.yaml
kubectl apply -f ./prometheus_adapter/prometheus_adapter.yaml
cd ../

# 部署gpu的监控
kubectl apply -f gpu/nvidia-device-plugin.yml
kubectl apply -f gpu/dcgm-exporter.yaml

# 部署volcano
kubectl delete -f volcano/volcano-development.yaml
kubectl apply -f volcano/volcano-development.yaml
kubectl wait crd/jobs.batch.volcano.sh --for condition=established --timeout=60s

# 部署istio
kubectl apply -f istio/install-crd.yaml
kubectl wait crd/envoyfilters.networking.istio.io --for condition=established --timeout=60s
# 在k8s 1.21-部署
#kubectl apply -f istio/install.yaml
# 在k8s 1.21+部署
# kubectl delete -f istio/install.yaml
kubectl apply -f istio/install-1.15.0.yaml

kubectl wait crd/virtualservices.networking.istio.io --for condition=established --timeout=60s
kubectl wait crd/gateways.networking.istio.io --for condition=established --timeout=60s

kubectl apply -f gateway.yaml
kubectl apply -f virtual.yaml

# 部署argo
kubectl apply -f argo/minio-pv-pvc-hostpath.yaml
kubectl apply -f argo/pipeline-runner-rolebinding.yaml
kubectl apply -f "$MODELONE_ARGO_MANIFEST_DIR/install-3.4.3-all.yaml"

# 部署trainjob:tfjob/pytorchjob/mpijob/mxnetjob/xgboostjobs/paddlepaddle
kubectl apply -f kubeflow/sa-rbac.yaml

kubectl apply -k kubeflow/train-operator/manifests/overlays/standalone


# 部署管理平台
kubectl delete configmap kubernetes-config -n infra
kubectl create configmap kubernetes-config --from-file=kubeconfig -n infra

kubectl delete configmap kubernetes-config -n pipeline
kubectl create configmap kubernetes-config --from-file=kubeconfig -n pipeline

kubectl delete configmap kubernetes-config -n automl
kubectl create configmap kubernetes-config --from-file=kubeconfig -n automl

kubectl create -f pv-pvc-infra.yaml
kubectl create -f pv-pvc-jupyter.yaml
kubectl create -f pv-pvc-automl.yaml
kubectl create -f pv-pvc-pipeline.yaml
kubectl create -f pv-pvc-service.yaml

kubectl apply -f "$MODELONE_KUBERNETES_MANIFEST"

# Keep the legacy node-address behavior without mutating the checked-in
# ConfigMap source or bypassing the rendered release manifest.
MODELONE_SERVICE_EXTERNAL_IP_VALUE="${MODELONE_SERVICE_EXTERNAL_IP:-$1}"
case "$MODELONE_SERVICE_EXTERNAL_IP_VALUE" in
  *[!A-Za-z0-9:.,_|-]*)
    echo "错误：MODELONE_SERVICE_EXTERNAL_IP 只能包含主机地址字符"
    exit 1
    ;;
esac
if [ -n "$MODELONE_SERVICE_EXTERNAL_IP_VALUE" ]; then
  kubectl set env deployment -n infra -l app.kubernetes.io/part-of=modelone \
    "MODELONE_SERVICE_EXTERNAL_IP=[\"$MODELONE_SERVICE_EXTERNAL_IP_VALUE\"]"
fi

# 配置入口
kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"externalIPs":["'"$1"'"]}}'
echo "打开网址：http://$1"

# ipvs模式启动配置入口
# kubectl patch svc istio-ingressgateway -n istio-system -p '{"spec":{"type":"NodePort"}}'
# nodeport=`kubectl get svc -n istio-system istio-ingressgateway -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}'`
# echo "打开网址：http://$1:$nodeport"
