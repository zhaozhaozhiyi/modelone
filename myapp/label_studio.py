"""Label Studio configuration and bounded REST adapter.

Credentials belong to the caller. No shared administrator token, database
access or credentials in URLs are used by this adapter.
"""
import json
import os
from urllib.parse import urlsplit

import requests


class LabelStudioError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def integration_config(environ=None):
    env = os.environ if environ is None else environ
    enabled = env.get('MODELONE_LABEL_STUDIO_ENABLED', 'false').lower() in ('true', '1')
    url = env.get('MODELONE_LABEL_STUDIO_INTERNAL_URL', 'http://label-studio:8080').rstrip('/')
    if enabled:
        validate_url(url)
    return {'LABEL_STUDIO_ENABLED': enabled,
            'LABEL_STUDIO_INTERNAL_URL': url,
            'LABEL_STUDIO_PUBLIC_URL': '/labelstudio/',
            'LABEL_STUDIO_TIMEOUT': (5, 60)}


def validate_url(url):
    try:
        parsed = urlsplit(url)
        valid = (parsed.scheme in ('http', 'https') and parsed.hostname
                 and not parsed.username and not parsed.password
                 and not parsed.query and not parsed.fragment and parsed.port != 0
                 and not any(char.isspace() for char in url))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('Label Studio internal URL must be an HTTP(S) service URL without credentials or query parameters')


class LabelStudioClient:
    MAX_RESPONSE = 64 * 1024 * 1024

    def __init__(self, base_url, authorization=None, timeout=(5, 60), session=None):
        validate_url(base_url)
        self.base_url = base_url.rstrip('/')
        self.authorization = authorization
        self.timeout = timeout
        self.session = session or requests.Session()
        # Service-to-service traffic must not leak tokens to an environment proxy.
        self.session.trust_env = False

    def close(self):
        self.session.close()

    def _call(self, method, path, params=None, data=None, authorization=None):
        headers = {'Accept': 'application/json'}
        if authorization:
            headers['Authorization'] = authorization
        try:
            with self.session.request(method, self.base_url + path, headers=headers,
                                      params=params, json=data, timeout=self.timeout,
                                      allow_redirects=False, stream=True) as response:
                if not 200 <= response.status_code < 300:
                    status = response.status_code if response.status_code in (400, 401, 403, 404, 409, 413, 429) else 502
                    raise LabelStudioError('标注服务拒绝请求，请检查令牌、项目权限和输入格式', status)
                body = bytearray()
                for chunk in response.iter_content(65536):
                    body.extend(chunk)
                    if len(body) > self.MAX_RESPONSE:
                        raise LabelStudioError('标注结果超过同步导出限制，请在标注平台使用分批或异步导出', 413)
                return bytes(body)
        except requests.Timeout:
            raise LabelStudioError('标注服务请求超时', 504) from None
        except requests.RequestException:
            raise LabelStudioError('标注服务暂时不可用', 503) from None

    @staticmethod
    def _json(body):
        try:
            return json.loads(body)
        except (ValueError, UnicodeError):
            raise LabelStudioError('标注服务返回了无效的 JSON') from None

    def health(self):
        self._call('GET', '/health')
        return {'available': True}

    def _credentials(self):
        auth = self.authorization or ''
        scheme, _, token = auth.partition(' ')
        if scheme not in ('Token', 'Bearer', 'Refresh') or not token or len(token) > 8192 or any(c.isspace() for c in token):
            raise LabelStudioError('请通过 X-Label-Studio-Authorization 提供自己的标注服务令牌', 401)
        if scheme == 'Refresh':
            result = self._json(self._call('POST', '/api/token/refresh/', data={'refresh': token}))
            access = result.get('access') if isinstance(result, dict) else None
            if not isinstance(access, str) or not access or any(c.isspace() for c in access):
                raise LabelStudioError('标注服务没有返回有效的访问令牌')
            # The access token lives only in this request's client instance.
            self.authorization = 'Bearer ' + access
        return self.authorization

    def projects(self, page=1, page_size=20):
        return self._json(self._call('GET', '/api/projects/', params={'page': page, 'page_size': page_size}, authorization=self._credentials()))

    def create_project(self, data):
        return self._json(self._call('POST', '/api/projects/', data=data, authorization=self._credentials()))

    def project(self, project_id):
        return self._json(self._call('GET', '/api/projects/%d/' % project_id, authorization=self._credentials()))

    def import_tasks(self, project_id, tasks):
        return self._json(self._call('POST', '/api/projects/%d/import' % project_id,
                                    params={'return_task_ids': 'true'}, data=tasks, authorization=self._credentials()))

    def export_tasks(self, project_id, all_tasks=False):
        result = self._json(self._call('GET', '/api/projects/%d/export' % project_id,
                                      params={'exportType': 'JSON', 'download_all_tasks': str(all_tasks).lower()},
                                      authorization=self._credentials()))
        if not isinstance(result, list):
            raise LabelStudioError('标注导出结果不是任务数组')
        return result
