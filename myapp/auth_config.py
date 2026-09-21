"""Private authentication configuration. Never included in public brand data."""
import os
from pathlib import Path


def read_secret(name, minimum=32):
    value = os.environ.get(name, '')
    filename = os.environ.get(name + '_FILE', '')
    if value and filename:
        raise ValueError('Set only one of %s or %s_FILE' % (name, name))
    if filename:
        value = Path(filename).read_text(encoding='utf-8').strip()
    if len(value) < minimum or len(set(value)) < 8:
        raise ValueError('%s must contain at least %d characters from a generated secret' % (name, minimum))
    return value


def security_config():
    session_key = read_secret('MODELONE_SECRET_KEY')
    jwt_key = read_secret('MODELONE_JWT_KEY')
    if session_key == jwt_key:
        raise ValueError('Session and API signing keys must be different')
    ttl = int(os.environ.get('MODELONE_API_TOKEN_TTL_SECONDS', '2592000'))
    if not 60 <= ttl <= 31536000:
        raise ValueError('MODELONE_API_TOKEN_TTL_SECONDS must be between 60 and 31536000')
    return {'SECRET_KEY': session_key, 'JWT_PASSWORD': jwt_key,
            'API_TOKEN_TTL_SECONDS': ttl, 'SESSION_COOKIE_HTTPONLY': True,
            'SESSION_COOKIE_SAMESITE': 'Lax',
            'SESSION_COOKIE_SECURE': os.environ.get('MODELONE_COOKIE_SECURE', 'true' if os.environ.get('STAGE') == 'prod' else 'false').lower() == 'true'}
