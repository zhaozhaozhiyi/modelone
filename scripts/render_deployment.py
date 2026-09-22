#!/usr/bin/env python3
"""Render Compose and Kubernetes manifests from the shared brand configuration.

No cluster, registry or credentials are modified. Output belongs to this checkout.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import yaml
from image_bundle import image_mapping, rewrite_images

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modelone_brand', ROOT / 'myapp/brand.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

def render(output, release=False, image_plan=None):
    if release:
        brand.validate_release_settings()
        if image_plan is None:
            raise ValueError('--release requires --image-plan generated from the deployment manifests')
    if image_plan is not None and not image_plan.is_file():
        raise ValueError('image plan does not exist: ' + str(image_plan))
    if release and image_plan is not None:
        try:
            plan_data = json.loads(image_plan.read_text())
            plan_registry = plan_data.get('registry', '').rstrip('/')
        except (OSError, ValueError) as error:
            raise ValueError('invalid image plan: ' + str(error))
        configured_registry = brand.BRAND['image_registry'].rstrip('/')
        if plan_registry != configured_registry:
            raise ValueError('image plan registry does not match MODELONE_IMAGE_REGISTRY')
        target_prefix = configured_registry + '/modelone/'
        invalid_targets = [row.get('target', '') for row in plan_data.get('images', [])
                           if not row.get('target', '').startswith(target_prefix)]
        if invalid_targets:
            raise ValueError('image plan contains targets outside MODELONE_IMAGE_REGISTRY')
    output.mkdir(parents=True, exist_ok=True)
    env = {'MODELONE_' + key.upper(): value for key, value in brand.BRAND.items() if key != 'copyright'}
    compose = yaml.safe_load((ROOT / 'install/docker/docker-compose.yml').read_text())
    compose.pop('version', None)
    compose['name'] = brand.BRAND['deployment_name']
    if release:
        # Release output must run from the published images and an external
        # kubeconfig, rather than binding this checkout into containers.
        compose['volumes'] = {
            'modelone-kubeflow-data': {},
            'modelone-mysql-data': {},
        }
        compose['services']['mysql']['volumes'] = [
            'modelone-mysql-data:/var/lib/mysql',
        ]
        compose['services']['frontend']['volumes'] = []
        compose['services']['myapp']['volumes'] = [
            'modelone-kubeflow-data:/data/k8s/kubeflow',
            '${MODELONE_KUBECONFIG:-./kubeconfig}:/home/myapp/kubeconfig:ro',
        ]
    for service in compose['services'].values():
        image = service.get('image', '').replace('${MODELONE_IMAGE_PREFIX:-}', '')
        if image.startswith('modelone/'):
            service['image'] = brand.image_repository(image[len('modelone/'):])
        if service is compose['services']['myapp']:
            service.setdefault('environment', {}).update(env)
        volumes = []
        for mount in service.get('volumes', []):
            if isinstance(mount, str) and mount.startswith('.'):
                source, rest = mount.split(':', 1)
                mount = str((ROOT / 'install/docker' / source).resolve()) + ':' + rest
            volumes.append(mount)
        if volumes:
            service['volumes'] = volumes
    rendered = subprocess.check_output(['kubectl', 'kustomize', str(ROOT / 'install/kubernetes/cube/overlays')], text=True)
    manifests = list(yaml.safe_load_all(rendered))
    manifests.append({'apiVersion':'v1', 'kind':'ConfigMap', 'metadata':{'name':'modelone-brand', 'namespace':'infra'}, 'data':env})
    errors = brand.proxy_error_pages()
    error_dir = output / 'frontend-errors'
    error_dir.mkdir(parents=True, exist_ok=True)
    for filename, html in errors.items():
        (error_dir / filename).write_text(html, encoding='utf-8')
    # A relative delivery mount travels with the rendered Compose file.
    compose['services']['frontend'].setdefault('volumes', []).append(
        './frontend-errors:/data/web/static/modelone-errors:ro')
    manifests.append({'apiVersion': 'v1', 'kind': 'ConfigMap',
                      'metadata': {'name': 'modelone-error-pages', 'namespace': 'infra'}, 'data': errors})
    for doc in manifests:
        spec = doc.get('spec', {}).get('template', {}).get('spec', {})
        if doc.get('metadata', {}).get('name') == 'kubeflow-dashboard-frontend' and spec:
            spec.setdefault('volumes', []).append({'name': 'modelone-error-pages',
                                                  'configMap': {'name': 'modelone-error-pages'}})
        for container in spec.get('containers', []):
            image = container.get('image', '')
            if image.startswith('modelone/'):
                container['image'] = brand.image_repository(image[len('modelone/'):])
            container.setdefault('envFrom', []).append({'configMapRef':{'name':'modelone-brand'}})
            if doc.get('metadata', {}).get('name') == 'kubeflow-dashboard-frontend':
                container.setdefault('volumeMounts', []).append({'name': 'modelone-error-pages',
                    'mountPath': '/data/web/static/modelone-errors', 'readOnly': True})
            if doc.get('metadata', {}).get('name') != 'kubeflow-dashboard-frontend':
                secret_ref = {'secretRef': {'name': 'modelone-auth'}}
                if secret_ref not in container['envFrom']:
                    container['envFrom'].append(secret_ref)
    if image_plan:
        mapping = image_mapping(image_plan)
        rewrite_images(compose, mapping)
        rewrite_images(manifests, mapping)
    (output / 'compose.yaml').write_text(yaml.safe_dump(compose, allow_unicode=True, sort_keys=False))
    (output / 'kubernetes.yaml').write_text(yaml.safe_dump_all(manifests, allow_unicode=True, sort_keys=False))
    (output / 'brand.json').write_text(json.dumps(brand.public_brand(), ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/modelone')
    parser.add_argument('--release', action='store_true')
    parser.add_argument('--image-plan', type=Path, help='use enterprise image targets from a generated images.json')
    args = parser.parse_args()
    try:
        render(args.output, args.release, args.image_plan)
    except ValueError as error:
        parser.error(str(error))
    print('Rendered deployment files: ' + str(args.output))
