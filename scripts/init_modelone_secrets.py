#!/usr/bin/env python3
"""Create private deployment secrets locally without printing or overwriting them."""
import argparse
import json
import os
from pathlib import Path
import secrets


def generate(output, kubernetes=False):
    values = {name: secrets.token_urlsafe(48) for name in
              ('MODELONE_SECRET_KEY', 'MODELONE_JWT_KEY', 'MODELONE_ADMIN_PASSWORD')}
    if kubernetes:
        content = json.dumps({'apiVersion': 'v1', 'kind': 'Secret',
                              'metadata': {'name': 'modelone-auth', 'namespace': 'infra'},
                              'type': 'Opaque', 'stringData': values}, indent=2) + '\n'
    else:
        content = ''.join('%s=%s\n' % item for item in values.items())
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, 'w') as target:
        target.write(content)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--kubernetes', action='store_true', help='write a local Secret manifest instead of a Compose env file')
    args = parser.parse_args()
    generate(args.output, args.kubernetes)
    print('Private secrets saved: ' + str(args.output))
