"""Validation and HTTP contract for independently operated AIHub endpoints."""
import json
import os
import re
import ipaddress
import socket
from urllib.parse import urlsplit

import jsonschema
import requests


CATEGORIES = ('机器视觉', '语音', '自然语言', '多模态', '大模型', '其他')
VISIBILITIES = ('public', 'project', 'private')
SLUG_PATTERN = re.compile(r'^[a-z][a-z0-9-]{2,79}$')
VERSION_PATTERN = re.compile(r'^[0-9A-Za-z][0-9A-Za-z._-]{0,39}$')
ENV_PATTERN = re.compile(r'^[A-Z][A-Z0-9_]{0,99}$')


class HubError(Exception):
    def __init__(self, message, status=400, code='invalid_request'):
        super().__init__(message)
        self.status = status
        self.code = code


def validate_application(data):
    if not isinstance(data, dict):
        raise HubError('请提交应用信息对象')
    allowed = {'slug', 'version', 'name', 'summary', 'category', 'task', 'model_source',
               'license_name', 'weight_digest', 'visibility',
               'project_id', 'input_schema', 'output_schema', 'endpoint_url',
               'endpoint_revision', 'credential_env'}
    if set(data) - allowed:
        raise HubError('应用信息包含不支持的字段')

    def string(key, limit, required=True):
        value = data.get(key, '')
        if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
            raise HubError('%s 无效' % key)
        return value.strip()

    values = {key: string(key, limit, required) for key, limit, required in (
        ('slug', 80, True), ('version', 40, True), ('name', 200, True),
        ('summary', 2000, False), ('category', 40, True), ('task', 100, False),
        ('model_source', 500, True), ('license_name', 100, True), ('weight_digest', 200, False),
        ('endpoint_url', 500, True), ('endpoint_revision', 200, True),
        ('credential_env', 100, False))}
    if not SLUG_PATTERN.fullmatch(values['slug']) or not VERSION_PATTERN.fullmatch(values['version']):
        raise HubError('应用 ID 或版本格式无效')
    if values['category'] not in CATEGORIES:
        raise HubError('应用分类无效')
    source = urlsplit(values['model_source'])
    if source.scheme not in ('http', 'https') or not source.hostname or source.username or source.password:
        raise HubError('模型来源必须是 HTTP(S) 地址')
    visibility = data.get('visibility', 'public')
    if visibility not in VISIBILITIES:
        raise HubError('可见范围无效')
    values['visibility'] = visibility
    project_id = data.get('project_id')
    if visibility == 'project':
        if isinstance(project_id, bool) or not isinstance(project_id, int) or project_id < 1:
            raise HubError('项目可见应用必须指定项目 ID')
    elif project_id not in (None, ''):
        raise HubError('只有项目可见应用可以指定项目 ID')
    values['project_id'] = project_id if visibility == 'project' else None

    parsed = urlsplit(values['endpoint_url'])
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username
            or parsed.password or parsed.query or parsed.fragment):
        raise HubError('运行端点必须是不含凭据、查询参数的 HTTP(S) 地址')
    values['endpoint_url'] = values['endpoint_url'].rstrip('/')
    if values['credential_env'] and not ENV_PATTERN.fullmatch(values['credential_env']):
        raise HubError('凭据环境变量名称无效')

    for key in ('input_schema', 'output_schema'):
        schema = data.get(key)
        if not isinstance(schema, dict):
            raise HubError('%s 必须是 JSON Schema 对象' % key)
        try:
            jsonschema.Draft202012Validator.check_schema(schema)
        except jsonschema.SchemaError:
            raise HubError('%s 不是有效的 JSON Schema' % key) from None
        values[key] = schema
    input_schema = values['input_schema']
    if input_schema.get('type') != 'object' or not isinstance(input_schema.get('properties'), dict):
        raise HubError('输入 Schema 必须描述对象及其 properties')
    if not input_schema['properties'] or len(input_schema['properties']) > 20:
        raise HubError('输入字段数量须为 1–20 个')
    if any(not isinstance(spec, dict) or spec.get('type') not in
           ('string', 'number', 'integer', 'boolean') for spec in input_schema['properties'].values()):
        raise HubError('首期输入字段仅支持文本、数字和布尔值')
    return values


def validate_endpoint_destination(url, allowed_hosts):
    parsed = urlsplit(url)
    host = parsed.hostname
    if not host or host not in allowed_hosts:
        raise HubError('运行端点主机不在允许列表中', 403, 'endpoint_not_allowed')
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None
    if literal is not None and (literal.is_loopback or literal.is_link_local or literal.is_multicast or literal.is_unspecified):
        raise HubError('运行端点地址不可用', 403, 'endpoint_not_allowed')
    if literal is None:
        try:
            addresses = socket.getaddrinfo(host, parsed.port or (443 if parsed.scheme == 'https' else 80),
                                            type=socket.SOCK_STREAM)
        except OSError:
            raise HubError('运行端点无法解析', 502, 'endpoint_unavailable') from None
        if not addresses:
            raise HubError('运行端点地址不可用', 403, 'endpoint_not_allowed')
        for address in addresses:
            ip = ipaddress.ip_address(address[4][0])
            if ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_unspecified:
                raise HubError('运行端点解析到不可用地址', 403, 'endpoint_not_allowed')


def validate_inputs(schema, inputs):
    try:
        jsonschema.Draft202012Validator(schema).validate(inputs)
    except jsonschema.ValidationError as error:
        path = '.'.join(str(part) for part in error.absolute_path) or 'inputs'
        raise HubError('%s: %s' % (path, error.message)) from None


def _headers(version):
    headers = {'Accept': 'application/json'}
    if version.credential_env:
        token = os.environ.get(version.credential_env)
        if not token:
            raise HubError('运行端点凭据未配置', 503, 'endpoint_config')
        headers['Authorization'] = 'Bearer ' + token
    return headers


def _request(version, method, path, allowed_hosts, **kwargs):
    validate_endpoint_destination(version.endpoint_url, allowed_hosts)
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.request(method, version.endpoint_url + path, headers=_headers(version),
                                   timeout=(3, 30 if method == 'POST' else 5),
                                   allow_redirects=False, stream=True, **kwargs)
        if response.status_code >= 300:
            raise HubError('运行端点返回 HTTP %d' % response.status_code, 502, 'endpoint_error')
        chunks = []
        size = 0
        for chunk in response.iter_content(65536):
            size += len(chunk)
            if size > 2 * 1024 * 1024:
                raise HubError('运行端点响应超过 2 MiB', 502, 'endpoint_response')
            chunks.append(chunk)
        return json.loads(b''.join(chunks))
    except requests.Timeout:
        raise HubError('运行端点响应超时', 504, 'endpoint_timeout') from None
    except requests.RequestException:
        raise HubError('运行端点无法连接', 502, 'endpoint_unavailable') from None
    except (ValueError, UnicodeError):
        raise HubError('运行端点未返回 JSON', 502, 'endpoint_response') from None
    finally:
        session.close()


def verify_endpoint(version, allowed_hosts, check_health=False):
    metadata = _request(version, 'GET', '/metadata', allowed_hosts)
    if not isinstance(metadata, dict) or any((
        metadata.get('application_id') != version.slug,
        metadata.get('version') != version.version,
        metadata.get('revision') != version.endpoint_revision,
    )):
        raise HubError('运行端点修订与已登记版本不一致', 409, 'revision_mismatch')
    if check_health:
        health = _request(version, 'GET', '/health', allowed_hosts)
        if not isinstance(health, dict) or health.get('status') != 'ok':
            raise HubError('运行端点健康检查未通过', 503, 'endpoint_unhealthy')
    return metadata


def predict(version, inputs, allowed_hosts):
    result = _request(version, 'POST', '/predict', allowed_hosts, json={'inputs': inputs})
    if not isinstance(result, dict) or 'result' not in result:
        raise HubError('运行端点响应缺少 result', 502, 'endpoint_response')
    try:
        jsonschema.Draft202012Validator(json.loads(version.output_schema)).validate(result['result'])
    except jsonschema.ValidationError:
        raise HubError('运行端点输出不符合应用 Schema', 502, 'endpoint_response') from None
    return result['result']
