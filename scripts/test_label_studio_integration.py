#!/usr/bin/env python3
"""Offline regression tests for the optional Label Studio integration."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import sys
import types
import subprocess
import unittest
from unittest.mock import Mock, patch
from flask import Flask, g, request
import requests
import yaml

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = load('label_studio_adapter', ROOT / 'myapp/label_studio.py')
sso = load('label_studio_sso', ROOT / 'myapp/label_studio_sso.py')
renderer = load('label_studio_renderer', ROOT / 'scripts/render_label_studio.py')
initializer = load('label_studio_initializer', ROOT / 'scripts/init_label_studio.py')
with patch.dict(sys.modules, {'myapp': types.ModuleType('myapp'), 'myapp.label_studio': adapter,
                              'myapp.label_studio_sso': sso}):
    web = load('label_studio_web_test', ROOT / 'myapp/label_studio_web.py')


class LabelStudioIntegrationTests(unittest.TestCase):
    def test_source_lock_and_fetch_are_pinned(self):
        lock = json.loads((ROOT / 'integrations/label-studio/upstream.json').read_text())
        checkout = ROOT / lock['source_directory']
        self.assertEqual(lock['tag'], '1.23.2')
        self.assertEqual(lock['license'], 'Apache-2.0')
        self.assertEqual(len(lock['commit']), 40)
        if (checkout / '.git').exists():
            commit = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
            self.assertEqual(commit, lock['commit'])

    def test_urls_and_tokens_fail_closed(self):
        for url in ('label-studio:8080', 'http://user:pass@label-studio:8080',
                    'http://label-studio:8080?token=x', 'http://label studio:8080'):
            with self.assertRaises(ValueError):
                adapter.validate_url(url)
        for auth in ('Token', 'Token a b', 'Basic secret', 'Bearer ' + 'x' * 8193):
            client = adapter.LabelStudioClient('http://label-studio:8080', auth, session=Mock())
            with self.assertRaises(adapter.LabelStudioError):
                client._credentials()

    def test_client_uses_user_token_and_rejects_redirects(self):
        session = Mock()
        response = Mock(status_code=200)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.iter_content.return_value = [b'[]']
        session.request.return_value = response
        client = adapter.LabelStudioClient('http://label-studio:8080', 'Token personal', session=session)
        self.assertEqual(client.projects(), [])
        call = session.request.call_args.kwargs
        self.assertEqual(call['headers']['Authorization'], 'Token personal')
        self.assertFalse(call['allow_redirects'])

    def test_response_limits_and_errors_do_not_expose_credentials(self):
        session = Mock()
        response = Mock(status_code=302)
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        session.request.return_value = response
        client = adapter.LabelStudioClient('http://label-studio:8080', 'Token private', session=session)
        with self.assertRaises(adapter.LabelStudioError) as result:
            client.projects()
        self.assertEqual(result.exception.status, 502)
        self.assertNotIn('private', str(result.exception))
        response.status_code = 200
        response.iter_content.return_value = [b'x' * 11]
        client.MAX_RESPONSE = 10
        with self.assertRaises(adapter.LabelStudioError) as result:
            client.projects()
        self.assertEqual(result.exception.status, 413)
        for error, status in ((requests.Timeout('private'), 504), (requests.ConnectionError('private'), 503)):
            session.request.side_effect = error
            with self.assertRaises(adapter.LabelStudioError) as result:
                client.projects()
            self.assertEqual(result.exception.status, status)
            self.assertNotIn('private', str(result.exception))

    def test_refresh_token_is_exchanged_and_not_reused_as_access_token(self):
        session = Mock()
        def response(body):
            result = Mock(status_code=200)
            result.__enter__ = Mock(return_value=result)
            result.__exit__ = Mock(return_value=False)
            result.iter_content.return_value = [body]
            return result
        session.request.side_effect = [response(b'{"access":"short-lived-access"}'), response(b'[]')]
        client = adapter.LabelStudioClient('http://label-studio:8080', 'Refresh personal-token', session=session)
        self.assertEqual(client.projects(), [])
        first, second = session.request.call_args_list
        self.assertEqual(first.kwargs['json'], {'refresh': 'personal-token'})
        self.assertNotIn('Authorization', first.kwargs['headers'])
        self.assertEqual(second.kwargs['headers']['Authorization'], 'Bearer short-lived-access')

    def test_private_secrets_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'label.env'
            initializer.generate(path, 'https://ai.example.com/labelstudio', 'a@example.com')
            before = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            with self.assertRaises(FileExistsError):
                initializer.generate(path, 'https://ai.example.com/labelstudio', 'a@example.com')
            self.assertEqual(path.read_bytes(), before)
            self.assertIn('LABEL_STUDIO_SSO_SECRET=', before.decode())

    def test_sso_assertion_uses_short_lived_signed_identity(self):
        user = types.SimpleNamespace(get_id=lambda: 7, username='annotator')
        token = sso.sign_user(user, secret='s' * 48, now=100)
        self.assertEqual(len(token.split('.')), 2)
        self.assertNotIn('annotator', token)
        with self.assertRaises(ValueError):
            sso.sign_user(user, secret='too-short', now=100)

    def test_rendered_compose_adds_services_without_replacing_base_mounts(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory) / 'base.yaml'
            out = Path(directory) / 'out.yaml'
            base.write_text('''services:\n  frontend:\n    image: frontend\n    volumes:\n      - ./config:/etc/nginx/conf.d/default.conf\n  myapp:\n    image: backend\n    volumes:\n      - ./data:/data\n''')
            (base.parent / 'config').write_text('server {\n}\n')
            renderer.render_compose(base, out)
            data = yaml.safe_load(out.read_text())
            self.assertIn('label-studio', data['services'])
            self.assertIn('label-studio-db', data['services'])
            self.assertIn('MODELONE_LABEL_STUDIO_ENABLED', data['services']['myapp']['environment'])
            self.assertIn('MODELONE_LABEL_STUDIO_SSO_SECRET', data['services']['myapp']['environment'])
            self.assertEqual(data['services']['label-studio']['environment']['DJANGO_SETTINGS_MODULE'],
                             'core.settings.modelone')
            self.assertTrue(any('modelone_sso.py' in volume for volume in data['services']['label-studio']['volumes']))
            self.assertTrue(str(data['services']['frontend']['volumes'][0]).startswith('/'))
            self.assertIn('include /etc/nginx/modelone-integrations/*.conf;',
                          (out.parent / 'nginx-label-studio.conf').read_text())
            self.assertNotIn('label-studio-gateway', data['services'])
            self.assertNotIn('ports', data['services']['label-studio'])
            self.assertEqual(data['services']['myapp']['volumes'], [str((base.parent / 'data').resolve()) + ':/data'])

    def test_rendering_release_with_image_owned_nginx_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            base, out = Path(directory) / 'base.yaml', Path(directory) / 'delivery/addon.yaml'
            base.write_text('services:\n  frontend:\n    image: frontend\n  myapp:\n    image: backend\n')
            renderer.render_compose(base, out)
            volumes = yaml.safe_load(out.read_text())['services']['frontend']['volumes']
            self.assertTrue(any(':/etc/nginx/conf.d/default.conf:ro' in v for v in volumes))

    def test_kubernetes_rendering_patches_gateway_and_scopes_secrets(self):
        with tempfile.TemporaryDirectory() as directory:
            base, out = Path(directory) / 'base.yaml', Path(directory) / 'addon.yaml'
            docs = [
                {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': 'nginx-configmap', 'namespace': 'infra'}, 'data': {'default.conf': 'server {}'}},
                *[{'apiVersion': 'apps/v1', 'kind': 'Deployment', 'metadata': {'name': name, 'namespace': 'infra'},
                   'spec': {'template': {'spec': {'containers': [{'name': name, 'image': 'example'}]}}}}
                  for name in ('kubeflow-dashboard', 'kubeflow-dashboard-frontend')]]
            base.write_text(yaml.safe_dump_all(docs))
            renderer.render_kubernetes(base, out, '10.96.0.10')
            result = list(yaml.safe_load_all(out.read_text()))
            proxy = next(d for d in result if d['metadata']['name'] == 'modelone-label-studio-proxy')
            self.assertIn('resolver 10.96.0.10', proxy['data']['label-studio.conf'])
            self.assertIn('label-studio.kubeflow.svc.cluster.local', proxy['data']['label-studio.conf'])
            self.assertIn('modelone-compact.css', proxy['data']['label-studio.conf'])
            self.assertIn('[data-testid="resources-card"]', proxy['data']['compact.css'])
            self.assertIn('[data-testid="dm-connect-source-storage-button"]', proxy['data']['compact.css'])
            self.assertIn('.lsf-empty-projects-page__heidi', proxy['data']['compact.css'])
            self.assertIn('img[alt="Heidi looking for projects"]', proxy['data']['compact.css'])
            self.assertIn('.lsf-menu-header__trigger', proxy['data']['compact.css'])
            self.assertIn('display: none !important', proxy['data']['compact.css'])
            self.assertIn('.lsf-menu-header__context', proxy['data']['compact.css'])
            self.assertIn('--modelone-bg: #f5f6f7', proxy['data']['compact.css'])
            self.assertIn('--modelone-surface-selected: #e9eaec', proxy['data']['compact.css'])
            self.assertIn('.lsf-radio-group-dm__button_checked', proxy['data']['compact.css'])
            self.assertIn('.lsf-menu-header__user', proxy['data']['compact.css'])
            self.assertIn('.lsf-spinner-ls__body', proxy['data']['compact.css'])
            self.assertIn('animation: modelone-loading-spin', proxy['data']['compact.css'])
            self.assertIn("'Create Project': '创建项目'", proxy['data']['locale-zh.js'])
            self.assertIn("'Home': '首页'", proxy['data']['locale-zh.js'])
            self.assertIn('从电脑上传文件即可开始', proxy['data']['locale-zh.js'])
            self.assertNotIn('（仅企业版）', proxy['data']['locale-zh.js'])
            self.assertIn("'Connect Model': '连接模型'", proxy['data']['locale-zh.js'])
            self.assertIn("'import button': '导入'", proxy['data']['locale-zh.js'])
            self.assertIn("'Use image from': '图像来源'", proxy['data']['locale-zh.js'])
            self.assertIn("'Webhook': '事件回调'", proxy['data']['locale-zh.js'])
            self.assertIn('font-size: 14px', proxy['data']['compact.css'])
            self.assertIn('function hideEnterprise', proxy['data']['locale-zh.js'])
            self.assertIn('translateCompoundLabels', proxy['data']['locale-zh.js'])
            self.assertIn("location = /labelstudio/organization", proxy['data']['label-studio.conf'])
            self.assertIn("location = /labelstudio/ {", proxy['data']['label-studio.conf'])
            self.assertIn("return 302 /labelstudio/projects;", proxy['data']['label-studio.conf'])
            addon_settings = next(d for d in result if d['metadata']['name'] == 'modelone-label-studio-sso'
                                  and d['metadata']['namespace'] == 'kubeflow')
            self.assertIn('ModeloneSSOMiddleware', addon_settings['data']['modelone_sso.py'])
            backend = next(d for d in result if d['kind'] == 'Deployment'
                           and d['metadata']['name'] == 'kubeflow-dashboard')
            backend_env = backend['spec']['template']['spec']['containers'][0]['env']
            self.assertTrue(any(e['name'] == 'MODELONE_LABEL_STUDIO_SSO_SECRET' for e in backend_env))
            self.assertTrue(any(d['kind'] == 'PersistentVolumeClaim' for d in result))
            self.assertFalse(any(d['kind'] == 'Secret' for d in result))

    def test_kubernetes_secret_scopes_sso_to_both_services(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'secrets.json'
            initializer.generate(output, 'https://ai.example.com/labelstudio', 'admin@example.com', kubernetes=True)
            items = json.loads(output.read_text())['items']
            self.assertEqual({item['metadata']['namespace'] for item in items}, {'infra', 'kubeflow'})
            self.assertEqual(items[0]['stringData']['LABEL_STUDIO_SSO_SECRET'],
                             items[1]['stringData']['LABEL_STUDIO_SSO_SECRET'])


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.sso_env = patch.dict(os.environ, MODELONE_LABEL_STUDIO_SSO_SECRET='s' * 48)
        self.sso_env.start()
        self.app = Flask('label-studio-tests')
        self.app.config.update(adapter.integration_config({'MODELONE_LABEL_STUDIO_ENABLED': 'true'}))
        self.client_factory = Mock()
        self.adapter = self.client_factory.return_value
        @self.app.before_request
        def authentication_fixture():
            if request.headers.get('X-Test-Session') == 'active':
                g.user = types.SimpleNamespace(get_id=lambda: '1', active=True)
            elif request.headers.get('X-Test-Session') == 'inactive':
                g.user = types.SimpleNamespace(get_id=lambda: '1', active=False)
        web.register_label_studio_routes(self.app, self.client_factory)
        self.browser = self.app.test_client()
        self.headers = {'X-Test-Session': 'active', 'X-Label-Studio-Authorization': 'Refresh personal-token'}

    def tearDown(self):
        self.sso_env.stop()

    def test_gateway_requires_active_session_not_a_username_cookie(self):
        self.browser.set_cookie('myapp_username', 'admin')
        self.assertEqual(self.browser.get('/label_studio/api/access').status_code, 401)
        self.assertEqual(self.browser.get('/label_studio/api/access', headers={'X-Test-Session': 'inactive'}).status_code, 401)
        access = self.browser.get('/label_studio/api/access', headers=self.headers)
        self.assertEqual(access.status_code, 204)
        self.assertTrue(access.headers['X-Modelone-Assertion'])
        self.app.config['LABEL_STUDIO_ENABLED'] = False
        self.assertEqual(self.browser.get('/label_studio/api/access', headers=self.headers).status_code, 503)
        self.client_factory.assert_not_called()

    def test_import_validates_before_contacting_upstream_and_closes_client(self):
        for data in ({'data': {}}, [], [{'data': {}}], [{'data': {'text': 'x'}, 'annotations': []}]):
            self.assertEqual(self.browser.post('/label_studio/api/projects/1/import', json=data, headers=self.headers).status_code, 400)
        self.client_factory.assert_not_called()
        self.adapter.import_tasks.return_value = {'task_count': 1}
        tasks = [{'data': {'text': '示例'}}]
        result = self.browser.post('/label_studio/api/projects/1/import', json=tasks, headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.adapter.import_tasks.assert_called_once_with(1, tasks)
        self.adapter.close.assert_called_once()
        self.assertEqual(self.client_factory.call_args.kwargs['authorization'], 'Refresh personal-token')

    def test_invalid_json_pagination_and_export_parameters_are_rejected(self):
        self.assertEqual(self.browser.post('/label_studio/api/projects', data='{', content_type='application/json', headers=self.headers).status_code, 400)
        self.assertEqual(self.browser.get('/label_studio/api/projects?page_size=101', headers=self.headers).status_code, 400)
        self.assertEqual(self.browser.get('/label_studio/api/projects/1/export?all_tasks=1', headers=self.headers).status_code, 400)
        self.client_factory.assert_not_called()

    def test_export_preserves_annotations_and_defaults_to_completed_tasks(self):
        tasks = [{'data': {'text': 'x'}, 'annotations': [{'result': []}]}]
        self.adapter.export_tasks.return_value = tasks
        response = self.browser.get('/label_studio/api/projects/7/export', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json, tasks)
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertIn('modelone-labels-7.json', response.headers['Content-Disposition'])
        self.adapter.export_tasks.assert_called_once_with(7, False)

    def test_upstream_permission_denial_is_preserved_and_client_is_closed(self):
        self.adapter.project.side_effect = adapter.LabelStudioError('Denied', 403)
        response = self.browser.get('/label_studio/api/projects/5', headers=self.headers)
        self.assertEqual(response.status_code, 403)
        self.adapter.close.assert_called_once()


if __name__ == '__main__':
    unittest.main()
