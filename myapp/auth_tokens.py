"""Signed API credentials; the historical two-part token format stays usable."""
import time
import jwt

TASK_API_PATHS = ('/dataset_modelview/api/', '/project_modelview/api/',
                  '/training_model_modelview/api/', '/inferenceservice_modelview/api/')


def issue_token(username, key, ttl=2592000, scope='api'):
    now = int(time.time())
    token = jwt.encode({'sub': username, 'iat': now, 'exp': now + ttl,
                        'iss': 'modelone', 'aud': 'modelone-api', 'scope': scope}, key, algorithm='HS256')
    return token.split('.', 1)[1]


def token_subject(token, key, path=''):
    if not isinstance(token, str):
        return None
    if token.lower().startswith('bearer '):
        token = token[7:].strip()
    if token.count('.') == 1:
        token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' + token
    try:
        payload = jwt.decode(token, key, algorithms=['HS256'], issuer='modelone', audience='modelone-api',
                             options={'require': ['sub', 'iat', 'exp', 'scope']})
    except (jwt.InvalidTokenError, TypeError, ValueError):
        return None
    if payload['scope'] == 'task' and not path.startswith(TASK_API_PATHS):
        return None
    if payload['scope'] not in ('api', 'task'):
        return None
    return payload['sub'] if isinstance(payload['sub'], str) and payload['sub'] else None
