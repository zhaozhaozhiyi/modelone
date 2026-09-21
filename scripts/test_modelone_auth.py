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


if __name__ == '__main__':
    unittest.main()
