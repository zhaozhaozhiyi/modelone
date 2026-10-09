#!/usr/bin/env python3
"""Render an opt-in Label Studio add-on for an existing platform deployment.

Reads deployment files only. Does not start containers or modify a cluster.
"""
import argparse
import copy
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def render_compose(base_path, output):
    base = yaml.safe_load(base_path.read_text())
    addon = yaml.safe_load((ROOT / 'install/label-studio/compose.yaml').read_text())
    addon['services'].pop('label-studio-gateway')
    output.parent.mkdir(parents=True, exist_ok=True)
    if not {'myapp', 'frontend'} <= set(base.get('services', {})):
        raise ValueError('Base Compose must contain myapp and frontend services')
    if {'label-studio', 'label-studio-db'} & set(base['services']):
        raise ValueError('Label Studio services already exist in the base deployment')
    # Moving the output must not redirect existing data or configuration mounts.
    for service in base['services'].values():
        mounts = service.get('volumes', [])
        for index, mount in enumerate(mounts):
            if isinstance(mount, str) and mount.startswith('.'):
                source, rest = mount.split(':', 1)
                mounts[index] = str((base_path.parent / source).resolve()) + ':' + rest
    for name, service in addon['services'].items():
        base['services'][name] = copy.deepcopy(service)
    label_service = base['services']['label-studio']
    label_service['volumes'] = [
        str(ROOT / 'integrations/label-studio/modelone_settings.py') + ':/label-studio/label_studio/core/settings/modelone.py:ro'
        if ':/label-studio/label_studio/core/settings/modelone.py:ro' in mount else
        str(ROOT / 'integrations/label-studio/modelone_sso.py') + ':/label-studio/label_studio/modelone_sso.py:ro'
        if ':/label-studio/label_studio/modelone_sso.py:ro' in mount else mount
        for mount in label_service['volumes']]
    # The combined deployment exposes Label Studio only through the platform.
    base.setdefault('volumes', {}).update(addon['volumes'])
    base['services']['myapp'].setdefault('environment', {}).update({
        'MODELONE_LABEL_STUDIO_ENABLED': 'true',
        'MODELONE_LABEL_STUDIO_INTERNAL_URL': 'http://label-studio:8080',
        'MODELONE_LABEL_STUDIO_SSO_SECRET': '${LABEL_STUDIO_SSO_SECRET:?Generate private Label Studio settings first}'})
    snippet = ROOT / 'integrations/label-studio/nginx.conf'
    # Keep the base frontend config unchanged. The optional include is written
    # beside the rendered Compose file and mounted only in this add-on.
    config_mount = next((m for m in base['services']['frontend'].get('volumes', [])
                         if isinstance(m, str) and ':/etc/nginx/conf.d/default.conf' in m), None)
    source_path = (Path(config_mount.split(':', 1)[0]) if config_mount
                   else ROOT / 'install/docker/dockerFrontend/nginx.80.conf')
    nginx_config = source_path.read_text()
    include = '    include /etc/nginx/modelone-integrations/*.conf;'
    if include not in nginx_config:
        nginx_config = nginx_config.replace('server {', 'server {\n' + include, 1)
    rendered_config = output.parent.resolve() / 'nginx-label-studio.conf'
    rendered_config.write_text(nginx_config)
    base['services']['frontend']['volumes'] = [
        (str(rendered_config) + ':/etc/nginx/conf.d/default.conf:ro') if mount == config_mount else mount
        for mount in base['services']['frontend'].get('volumes', [])]
    if not config_mount:
        base['services']['frontend']['volumes'].append(str(rendered_config) + ':/etc/nginx/conf.d/default.conf:ro')
    base['services']['frontend'].setdefault('volumes', []).append(
        str(snippet.parent) + ':/etc/nginx/modelone-integrations:ro')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump(base, allow_unicode=True, sort_keys=False))


def render_kubernetes(base_path, output, resolver):
    import ipaddress
    ipaddress.IPv4Address(resolver)
    docs = list(yaml.safe_load_all(base_path.read_text()))
    if any(d and d.get('metadata', {}).get('name') == 'label-studio' for d in docs):
        raise ValueError('Label Studio already exists in the base deployment')
    addon = list(yaml.safe_load_all((ROOT / 'install/kubernetes/label-studio/deployment.yaml').read_text()))
    snippet = (ROOT / 'integrations/label-studio/nginx.conf').read_text().replace(
        '127.0.0.11', resolver).replace('label-studio:8080', 'label-studio.kubeflow.svc.cluster.local:8080').replace(
        'http://myapp:80/', 'http://kubeflow-dashboard.infra:80/')
    docs.append({'apiVersion': 'v1', 'kind': 'ConfigMap',
                 'metadata': {'name': 'modelone-label-studio-proxy', 'namespace': 'infra'},
                 'data': {
                     'label-studio.conf': snippet,
                     'compact.css': (ROOT / 'integrations/label-studio/compact.css').read_text(),
                     'locale-zh.js': (ROOT / 'integrations/label-studio/locale-zh.js').read_text(),
                 }})
    docs.append({'apiVersion': 'v1', 'kind': 'ConfigMap',
                 'metadata': {'name': 'modelone-label-studio-sso', 'namespace': 'kubeflow'},
                 'data': {
                     'modelone_settings.py': (ROOT / 'integrations/label-studio/modelone_settings.py').read_text(),
                     'modelone_sso.py': (ROOT / 'integrations/label-studio/modelone_sso.py').read_text(),
                 }})
    found = set()
    for doc in docs:
        if not doc:
            continue
        name = doc.get('metadata', {}).get('name')
        if doc['kind'] == 'ConfigMap' and name == 'nginx-configmap':
            config = doc['data']['default.conf']
            if '/etc/nginx/modelone-integrations/*.conf' not in config:
                doc['data']['default.conf'] = config.replace('server {', 'server {\n        include /etc/nginx/modelone-integrations/*.conf;', 1)
            found.add('nginx')
        if doc['kind'] == 'Deployment' and name in ('kubeflow-dashboard', 'kubeflow-dashboard-frontend'):
            spec = doc['spec']['template']['spec']
            if name == 'kubeflow-dashboard':
                spec['containers'][0].setdefault('env', []).extend([
                    {'name': 'MODELONE_LABEL_STUDIO_ENABLED', 'value': 'true'},
                    {'name': 'MODELONE_LABEL_STUDIO_INTERNAL_URL', 'value': 'http://label-studio.kubeflow.svc.cluster.local:8080'},
                    {'name': 'MODELONE_LABEL_STUDIO_SSO_SECRET', 'valueFrom': {'secretKeyRef': {
                        'name': 'modelone-label-studio-sso', 'key': 'LABEL_STUDIO_SSO_SECRET'}}}])
                found.add('backend')
            else:
                spec.setdefault('volumes', []).append({'name': 'label-studio-proxy', 'configMap': {'name': 'modelone-label-studio-proxy'}})
                spec['containers'][0].setdefault('volumeMounts', []).append(
                    {'name': 'label-studio-proxy', 'mountPath': '/etc/nginx/modelone-integrations', 'readOnly': True})
                found.add('frontend')
    if found != {'nginx', 'backend', 'frontend'}:
        raise ValueError('Base Kubernetes deployment must contain the platform backend, frontend and nginx-configmap')
    label_deployment = next(d for d in addon if d and d.get('kind') == 'Deployment'
                            and d.get('metadata', {}).get('name') == 'label-studio')
    label_spec = label_deployment['spec']['template']['spec']
    label_container = label_spec['containers'][0]
    label_container.setdefault('env', []).extend([
        {'name': 'DJANGO_SETTINGS_MODULE', 'value': 'core.settings.modelone'},
        {'name': 'MODELONE_LABEL_STUDIO_SSO_SECRET', 'valueFrom': {'secretKeyRef': {
            'name': 'modelone-label-studio', 'key': 'LABEL_STUDIO_SSO_SECRET'}}},
    ])
    label_spec.setdefault('volumes', []).append({'name': 'modelone-sso', 'configMap': {'name': 'modelone-label-studio-sso'}})
    label_container.setdefault('volumeMounts', []).extend([
        {'name': 'modelone-sso', 'mountPath': '/label-studio/label_studio/core/settings/modelone.py',
         'subPath': 'modelone_settings.py', 'readOnly': True},
        {'name': 'modelone-sso', 'mountPath': '/label-studio/label_studio/modelone_sso.py',
         'subPath': 'modelone_sso.py', 'readOnly': True},
    ])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(yaml.safe_dump_all([d for d in docs if d] + addon, allow_unicode=True, sort_keys=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--compose-base', type=Path)
    mode.add_argument('--kubernetes-base', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cluster-dns', help='Cluster DNS IPv4 service address; required for Kubernetes')
    args = parser.parse_args()
    if args.kubernetes_base and not args.cluster_dns:
        parser.error('--cluster-dns is required for Kubernetes')
    if args.output.resolve() == (args.compose_base or args.kubernetes_base).resolve():
        parser.error('Use a separate output file to preserve the base deployment')
    if args.compose_base:
        render_compose(args.compose_base.resolve(), args.output)
    else:
        render_kubernetes(args.kubernetes_base, args.output, args.cluster_dns)
    print('Label Studio deployment saved: ' + str(args.output))
