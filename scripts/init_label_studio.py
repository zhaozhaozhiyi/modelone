#!/usr/bin/env python3
"""Generate NEW Label Studio credentials; never print or overwrite secrets."""
import argparse
import json
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit


def generate(output, host, email, kubernetes=False):
    parsed = urlsplit(host)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path.rstrip('/') != '/labelstudio'
            or any(c.isspace() for c in host)):
        raise ValueError('Public URL must be http(s)://host[:port]/labelstudio')
    if '@' not in email or any(c.isspace() for c in email):
        raise ValueError('Provide a valid initial administrator email')
    values = {'LABEL_STUDIO_HOST': host.rstrip('/'),
              'LABEL_STUDIO_ADMIN_EMAIL': email,
              'LABEL_STUDIO_ADMIN_PASSWORD': secrets.token_urlsafe(48),
              'LABEL_STUDIO_DB_PASSWORD': secrets.token_urlsafe(48),
              'LABEL_STUDIO_SSO_SECRET': secrets.token_urlsafe(48),
              'LABEL_STUDIO_COOKIE_SECURE': '1' if parsed.scheme == 'https' else '0'}
    if kubernetes:
        content = json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': [
            {'apiVersion': 'v1', 'kind': 'Secret',
             'metadata': {'name': 'modelone-label-studio', 'namespace': 'kubeflow'},
             'type': 'Opaque', 'stringData': values},
            {'apiVersion': 'v1', 'kind': 'Secret',
             'metadata': {'name': 'modelone-label-studio-sso', 'namespace': 'infra'},
             'type': 'Opaque', 'stringData': {'LABEL_STUDIO_SSO_SECRET': values['LABEL_STUDIO_SSO_SECRET']}},
        ]}, indent=2) + '\n'
    else:
        content = ''.join('%s=%s\n' % item for item in values.items())
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(output), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--host', required=True)
    parser.add_argument('--email', required=True)
    parser.add_argument('--kubernetes', action='store_true')
    args = parser.parse_args()
    generate(args.output, args.host, args.email, args.kubernetes)
    print('Private Label Studio settings saved: ' + str(args.output))
