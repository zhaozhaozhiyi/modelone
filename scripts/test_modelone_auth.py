"""Security regression tests independent of the Flask application runtime."""
import importlib.util
import json
import os
from pathlib import Path
import secrets
import tempfile
import time
import unittest
from unittest.mock import patch
import jwt

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tokens = load(ROOT / 'myapp/auth_tokens.py')
config = load(ROOT / 'myapp/auth_config.py')
initializer = load(ROOT / 'scripts/init_modelone_secrets.py')


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.key = secrets.token_urlsafe(48)

    def test_signed_short_full_and_bearer_tokens(self):
        short = tokens.issue_token('operator', self.key)
        full = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' + short
        for token in (short, full, 'Bearer ' + full):
            self.assertEqual(tokens.token_subject(token, self.key), 'operator')

    def test_username_expired_wrong_key_and_invalid_claims_are_denied(self):
        now = int(time.time())
        payload = {'sub': 'admin', 'iat': now, 'exp': now + 600, 'iss': 'modelone', 'aud': 'modelone-api', 'scope': 'api'}
        for token in ('admin', tokens.issue_token('admin', secrets.token_urlsafe(48)),
                      jwt.encode({**payload, 'exp': now - 10}, self.key, algorithm='HS256'),
                      jwt.encode({**payload, 'iss': 'unknown'}, self.key, algorithm='HS256'),
                      jwt.encode({**payload, 'sub': 1}, self.key, algorithm='HS256'),
                      jwt.encode({**payload, 'iat': None}, self.key, algorithm='HS256'),
                      jwt.encode({**payload, 'exp': None}, self.key, algorithm='HS256'),
                      jwt.encode({'sub': 'admin'}, self.key, algorithm='HS256')):
            self.assertIsNone(tokens.token_subject(token, self.key))

    def test_task_tokens_cannot_create_sessions_or_manage_users(self):
        token = tokens.issue_token('creator', self.key, scope='task')
        for path in tokens.TASK_API_PATHS:
            self.assertEqual(tokens.token_subject(token, self.key, path + '1'), 'creator')
        for path in ('/login/api/', '/users/', '/k8s/delete/pod/', '/dataset_modelview/api-evil/'):
            self.assertIsNone(tokens.token_subject(token, self.key, path))

    def test_missing_weak_or_reused_keys_fail_closed(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                config.security_config()
        with patch.dict(os.environ, {'MODELONE_SECRET_KEY': 'x'*48, 'MODELONE_JWT_KEY': self.key}, clear=True):
            with self.assertRaises(ValueError):
                config.security_config()
        with patch.dict(os.environ, {'MODELONE_SECRET_KEY': self.key, 'MODELONE_JWT_KEY': self.key}, clear=True):
            with self.assertRaises(ValueError):
                config.security_config()

    def test_secret_files_and_production_cookie_defaults(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'key'
            path.write_text(self.key + '\n')
            with patch.dict(os.environ, {'MODELONE_SECRET_KEY_FILE': str(path), 'MODELONE_JWT_KEY': secrets.token_urlsafe(48), 'STAGE': 'prod'}, clear=True):
                result = config.security_config()
                self.assertEqual(result['SECRET_KEY'], self.key)
                self.assertTrue(result['SESSION_COOKIE_SECURE'])
                self.assertTrue(result['SESSION_COOKIE_HTTPONLY'])
                self.assertEqual(result['SESSION_COOKIE_SAMESITE'], 'Lax')

    def test_secret_generation_is_private_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'auth.env'
            initializer.generate(path)
            before = path.read_bytes()
            self.assertEqual(path.stat().st_mode & 0o077, 0)
            with self.assertRaises(FileExistsError):
                initializer.generate(path)
            self.assertEqual(path.read_bytes(), before)
            env = dict(line.split('=', 1) for line in before.decode().splitlines())
            with patch.dict(os.environ, env, clear=True):
                self.assertNotEqual(config.security_config()['SECRET_KEY'], env['MODELONE_JWT_KEY'])
            secret = Path(directory) / 'secret.json'
            initializer.generate(secret, kubernetes=True)
            self.assertEqual(json.loads(secret.read_text())['metadata']['name'], 'modelone-auth')

            new_install = Path(directory) / 'new-install.json'
            initializer.generate(new_install, fresh_kubernetes=True)
            manifest = json.loads(new_install.read_text())
            self.assertEqual(manifest['kind'], 'List')
            self.assertEqual({item['metadata']['name'] for item in manifest['items']},
                             {'modelone-auth', 'modelone-infrastructure', 'modelone-mysql'})

            source = Path(directory) / 'infrastructure.json'
            source.write_text(json.dumps({'MYSQL_SERVICE': 'mysql+pymysql://root:p%40ss@mysql-service.infra:3306/kubeflow',
                                          'REDIS_PASSWORD': 'redis-secret'}))
            imported = Path(directory) / 'imported.json'
            initializer.import_infrastructure(source, imported)
            self.assertEqual(json.loads(imported.read_text())['metadata']['name'], 'modelone-infrastructure')

    def test_deployment_does_not_ship_default_database_credentials(self):
        compose = (ROOT / 'install/docker/docker-compose.yml').read_text()
        overlay = (ROOT / 'install/kubernetes/cube/overlays/kustomization.yml').read_text()
        mysql = (ROOT / 'install/kubernetes/mysql/deploy.yaml').read_text()
        redis = (ROOT / 'install/kubernetes/redis/redis.yaml').read_text()
        services = (ROOT / 'myapp/init/init-service.json').read_text()
        argo = (ROOT / 'install/kubernetes/argo/workflow.yaml').read_text()
        example = (ROOT / 'myapp/example/pipeline/ml/init.py').read_text()
        grafana = (ROOT / 'install/kubernetes/prometheus/grafana/grafana.ini').read_text()
        grafana_secret = (ROOT / 'install/kubernetes/prometheus/grafana/grafana-admin-secret.yml').read_text()
        celery = (ROOT / 'myapp/tools/check_celery.py').read_text()
        rabbit = (ROOT / 'myapp/example/pipeline/offline-inference/predict_model.py').read_text()
        datax = (ROOT / 'myapp/example/pipeline/datax/mysql-csv.json').read_text()
        ml_datax = (ROOT / 'myapp/example/pipeline/ml/mysql-csv.json').read_text()
        batch_ssh = (ROOT / 'install/kubernetes/rancher/批量ssh/batch-ssh.sh').read_text()
        batch_init = (ROOT / 'install/kubernetes/rancher/批量ssh/init.sh').read_text()
        cluster = (ROOT / 'install/kubernetes/rancher/kubekey/config-cluster.yaml').read_text()
        cluster_offline = (ROOT / 'install/kubernetes/rancher/kubekey/config-cluster-offline.yaml').read_text()
        cluster_doc = (ROOT / 'install/kubernetes/rancher/kubekey/kubekey部署modelone.md').read_text()
        cluster_demo = (ROOT / 'install/kubernetes/rancher/cluster-demo.yaml').read_text()
        self.assertNotIn('MYSQL_ROOT_PASSWORD: admin', compose)
        self.assertNotIn('REDIS_PASSWORD: admin', compose)
        self.assertNotIn('REDIS_PASSWORD=admin', overlay)
        self.assertNotIn('PMA_PASSWORD=admin', services)
        self.assertNotIn('REDIS_PASSWORD=admin', services)
        self.assertNotIn('password: admin', argo)
        self.assertNotIn('root:admin', example)
        self.assertNotIn('admin_password = admin', grafana)
        self.assertNotIn('secret_key = SW2YcwTIb9zpOOhoPsMm', grafana)
        self.assertNotIn('password: YWRtaW4=', grafana_secret)
        self.assertIn('REPLACE_WITH_PRIVATE_GRAFANA_PASSWORD', grafana_secret)
        self.assertIn('REPLACE_WITH_PRIVATE_GRAFANA_SECRET_KEY', grafana_secret)
        self.assertIn('GF_SECURITY_SECRET_KEY', (ROOT / 'install/kubernetes/prometheus/grafana/grafana-dp.yml').read_text())
        self.assertNotIn("password='admin'", celery)
        self.assertIn("os.environ.get('REDIS_PASSWORD')", celery)
        self.assertNotIn("password='admin'", rabbit)
        self.assertIn('RABBIT_PASSWORD', rabbit)
        self.assertNotIn('"password": "admin"', datax)
        self.assertNotIn('"password": "admin"', ml_datax)
        self.assertIn('"username": "modelone"', datax)
        self.assertIn('"username": "modelone"', ml_datax)
        self.assertIn('MODELONE_NODE_IPS_FILE', batch_ssh)
        self.assertNotIn('PASSWORD="', batch_ssh)
        self.assertNotIn('Authorization:', batch_ssh)
        self.assertIn('RANCHER_AGENT_TOKEN', batch_init)
        self.assertNotIn('--token tpl', batch_init)
        self.assertNotIn('https://10.0.0.76', batch_init)
        for template in (cluster, cluster_offline, cluster_doc):
            self.assertNotIn('1qaz2wsx', template)
            self.assertNotIn('Qcloud@123', template)
        self.assertIn('REPLACE_WITH_PRIVATE_SSH_PASSWORD', cluster)
        self.assertNotIn('password: password', cluster_demo)
        self.assertNotIn('myaccesssecret', cluster_demo)
        self.assertIn('MODELONE_EXAMPLE_MYSQL_SERVICE', example)
        self.assertIn('__CONFIGURE_BEFORE_DEPLOY__', services)
        self.assertIn('secretKeyRef', mysql)
        self.assertIn('secretKeyRef', redis)


if __name__ == '__main__':
    unittest.main()
