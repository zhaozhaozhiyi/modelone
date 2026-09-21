#!/usr/bin/env python3
"""Create private deployment secrets locally without printing or overwriting them."""
import argparse
import json
import os
from pathlib import Path
import secrets
from urllib.parse import quote, urlsplit


def secret_manifest(name, values):
    return {'apiVersion': 'v1', 'kind': 'Secret',
            'metadata': {'name': name, 'namespace': 'infra'},
            'type': 'Opaque', 'stringData': values}


def write_private(output, content):
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as target:
        target.write(content)


def generate(output, kubernetes=False, fresh_kubernetes=False):
    """Generate NEW installation credentials; never rotate an existing installation."""
    auth = {name: secrets.token_urlsafe(48) for name in
            ('MODELONE_SECRET_KEY', 'MODELONE_JWT_KEY', 'MODELONE_ADMIN_PASSWORD')}
    if kubernetes:
        content = json.dumps(secret_manifest('modelone-auth', auth), indent=2) + '\n'
    else:
        root_password, db_password, redis_password = (secrets.token_urlsafe(48) for _ in range(3))
        host = 'mysql-service.infra' if fresh_kubernetes else 'mysql'
        infrastructure = {'MYSQL_SERVICE': 'mysql+pymysql://modelone:%s@%s:3306/kubeflow?charset=utf8mb4' % (quote(db_password, safe=''), host),
                          'REDIS_PASSWORD': redis_password}
        if fresh_kubernetes:
            manifests = [secret_manifest('modelone-auth', auth),
                         secret_manifest('modelone-infrastructure', infrastructure),
                         secret_manifest('modelone-mysql', {'MYSQL_ROOT_PASSWORD': root_password, 'MYSQL_PASSWORD': db_password})]
            content = json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': manifests}, indent=2) + '\n'
        else:
            values = {**auth, 'MODELONE_MYSQL_USER': 'modelone',
                      'MODELONE_MYSQL_ROOT_PASSWORD': root_password,
                      'MODELONE_MYSQL_PASSWORD': db_password, **infrastructure}
            content = ''.join('%s=%s\n' % item for item in values.items())
    write_private(output, content)


def import_infrastructure(source, output):
    """Package existing service credentials without regenerating or changing them."""
    values = json.loads(source.read_text())
    keys = ('MYSQL_SERVICE', 'REDIS_PASSWORD')
    if not isinstance(values, dict) or set(values) != set(keys):
        raise ValueError('Source JSON must contain exactly MYSQL_SERVICE and REDIS_PASSWORD')
    if any(not isinstance(values[key], str) or not values[key] or '\n' in values[key] or '\r' in values[key] for key in keys):
        raise ValueError('Infrastructure values must be non-empty single-line strings')
    try:
        uri = urlsplit(values['MYSQL_SERVICE'])
        valid = uri.scheme == 'mysql+pymysql' and uri.hostname and uri.username and uri.password and uri.path.strip('/')
    except ValueError:
        valid = False
    if not valid:
        raise ValueError('MYSQL_SERVICE must be a complete mysql+pymysql connection URL')
    write_private(output, json.dumps(secret_manifest('modelone-infrastructure', values), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--kubernetes', action='store_true', help='generate only the authentication Secret for an installation with existing infrastructure')
    mode.add_argument('--kubernetes-new-install', action='store_true', help='generate authentication, MySQL and Redis Secrets for NEW empty services')
    mode.add_argument('--infrastructure-from-json', type=Path, help='package existing MYSQL_SERVICE and REDIS_PASSWORD from a private JSON file')
    args = parser.parse_args()
    if args.infrastructure_from_json:
        import_infrastructure(args.infrastructure_from_json, args.output)
    else:
        generate(args.output, args.kubernetes, args.kubernetes_new_install)
    print('Private secrets saved: ' + str(args.output))
