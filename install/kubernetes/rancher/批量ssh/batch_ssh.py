"""Run one selected installation stage over key-authenticated SSH, sequentially."""
import ipaddress
import json
import os
from pathlib import Path
import re
import shlex
import stat
import subprocess
import sys

FIELDS = {
    'STAGE', 'MODELONE_RANCHER_BUNDLE_DIR', 'MODELONE_NODE_INTERFACE',
    'MODELONE_NFS_SERVER', 'MODELONE_NFS_EXPORT',
    'RANCHER_SERVER_URL', 'RANCHER_AGENT_TOKEN', 'RANCHER_AGENT_CA_CHECKSUM',
    'RANCHER_AGENT_IMAGE',
}
STAGES = {'1', '11', '2', '22', '3', '33', '4', '44'}


def prepare(env):
    node_file = Path(env['MODELONE_NODE_IPS_FILE'])
    username = env['MODELONE_SSH_USER']
    if not re.fullmatch(r'[a-z_][a-z0-9_-]*', username):
        raise ValueError('Invalid SSH user name')
    nodes = []
    for line in node_file.read_text().splitlines():
        value = line.split('#', 1)[0].strip()
        if value:
            node = str(ipaddress.ip_address(value))
            if node not in nodes:
                nodes.append(node)
    if not nodes:
        raise ValueError('Node list is empty')
    private_file = Path(env['MODELONE_NODE_CONFIG_FILE'])
    if stat.S_IMODE(private_file.stat().st_mode) & 0o077:
        raise ValueError('Node configuration must be private (chmod 600)')
    config = json.loads(private_file.read_text())
    if not isinstance(config, dict) or not set(config).issubset(FIELDS):
        raise ValueError('Unsupported node configuration fields')
    if any(not isinstance(v, str) or '\x00' in v for v in config.values()):
        raise ValueError('Node configuration values must be strings without NUL')
    stage = config.get('STAGE', '')
    if stage not in STAGES:
        raise ValueError('Select an explicit supported STAGE')
    required = {'2': ['MODELONE_NFS_SERVER', 'MODELONE_NFS_EXPORT'],
                '3': ['MODELONE_RANCHER_BUNDLE_DIR'],
                '44': ['RANCHER_SERVER_URL', 'RANCHER_AGENT_TOKEN', 'RANCHER_AGENT_CA_CHECKSUM']}
    if any(not config.get(key) for key in required.get(stage, [])):
        raise ValueError('Required settings for the selected stage are missing')
    script = Path(__file__).with_name('init.sh').read_text()
    # Secrets travel only inside SSH's encrypted stdin, never in local argv,
    # a copied remote file, or terminal output. Quote each value as shell data.
    exports = '\n'.join('export ' + key + '=' + shlex.quote(value) for key, value in config.items())
    return username, nodes, 'set +x\nset -euo pipefail\n' + exports + '\n' + script


def deploy(env, run=subprocess.run):
    username, nodes, payload = prepare(env)
    failed = []
    for node in nodes:
        result = run(['ssh', '-T', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
                      '-o', 'ConnectTimeout=15', username + '@' + node, 'bash -s'],
                     input=payload, text=True, capture_output=True)
        if result.returncode:
            failed.append(node)
            print(node + ': failed (exit ' + str(result.returncode) + '); inspect the node service logs', file=sys.stderr)
        else:
            print(node + ': completed')
    if failed:
        print(str(len(failed)) + ' node(s) failed', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    try:
        sys.exit(deploy(os.environ))
    except (ValueError, OSError, KeyError):
        print('Invalid node configuration. Check MODELONE_NODE_IPS_FILE, MODELONE_SSH_USER, '
              'MODELONE_NODE_CONFIG_FILE, file permissions and the selected stage.', file=sys.stderr)
        sys.exit(2)
