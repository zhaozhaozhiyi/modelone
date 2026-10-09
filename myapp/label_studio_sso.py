"""Short-lived, proxy-only identity assertions for the Label Studio add-on."""
import base64
import hashlib
import hmac
import json
import os
import time


def sign_user(user, secret=None, now=None):
    secret = secret or os.environ.get('MODELONE_LABEL_STUDIO_SSO_SECRET', '')
    if len(secret) < 32:
        raise ValueError('Label Studio SSO secret is not configured')
    subject = str(user.get_id())
    username = str(getattr(user, 'username', '') or subject)
    if not subject or len(subject) > 100 or not username or len(username) > 200:
        raise ValueError('Invalid platform user identity')
    payload = {'aud': 'label-studio', 'sub': subject, 'username': username,
               'iat': int(time.time() if now is None else now)}
    data = base64.urlsafe_b64encode(json.dumps(payload, separators=(',', ':'), ensure_ascii=False).encode()).rstrip(b'=')
    signature = hmac.new(secret.encode(), data, hashlib.sha256).digest()
    return data.decode() + '.' + base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
