"""Initialize notebook files and optional, per-notebook SSH access."""
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys


def initialize(env, root=Path('/'), run=subprocess.run):
    def path(value):
        return root / str(value).lstrip('/')

    def command(*args, **kwargs):
        return run(list(args), check=True, **kwargs)

    # Stop the managed daemon before changing credentials, including on a retry.
    command('service', 'ssh', 'stop')
    config = path('/etc/ssh/sshd_config')
    config.parent.mkdir(parents=True, exist_ok=True)
    # A failed initialization must never fall back to an inherited SSH password.
    config.write_text('PermitRootLogin no\nPasswordAuthentication no\n'
                      'PermitEmptyPasswords no\nKbdInteractiveAuthentication no\n')

    username = env.get('USERNAME', '')
    if not re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9_.-]*', username):
        raise ValueError('USERNAME must be a single directory name')
    workspace = path('/mnt') / username
    workspace.mkdir(parents=True, exist_ok=True)
    examples = workspace / 'examples'
    if not examples.exists() and not examples.is_symlink():
        examples.symlink_to('/examples', target_is_directory=True)

    if env.get('MODELONE_NOTEBOOK_SPARK') == 'true':
        spark_file = path(env['SPARK_HOME']) / 'conf/spark-defaults.conf'
        settings = {
            'spark.ui.enabled': 'false',
            'spark.driver.port': env['PORT1'],
            'spark.blockManager.port': env['PORT2'],
            'spark.driver.bindAddress': '0.0.0.0',
            'spark.driver.host': env['SERVICE_EXTERNAL_IP'],
        }
        original = spark_file.read_text() if spark_file.exists() else ''
        lines = [line for line in original.splitlines()
                 if not re.match(r'^\s*(?:' + '|'.join(map(re.escape, settings)) + r')(?:\s|=)', line)]
        spark_file.parent.mkdir(parents=True, exist_ok=True)
        spark_file.write_text('\n'.join(lines + [f'{key}={value}' for key, value in settings.items()]) + '\n')

    password = env.get('NOTEBOOK_ROOT_PASSWORD', '')
    password_file = env.get('NOTEBOOK_ROOT_PASSWORD_FILE', '')
    keys_file = env.get('NOTEBOOK_SSH_PUBLIC_KEY_FILE', '')
    if password and password_file:
        raise ValueError('Set only one password source')
    if password_file:
        password = path(password_file).read_text().rstrip('\r\n')
        if not password:
            raise ValueError('Notebook password file is empty')
    if password and (len(password) < 16 or '\n' in password or '\r' in password):
        raise ValueError('Notebook SSH password must contain at least 16 characters on one line')
    if not password and not keys_file:
        print('SSH disabled: no per-notebook credentials configured; notebook files are ready')
        return

    port = env.get('SSH_PORT', '')
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError('SSH_PORT must be between 1 and 65535')
    runtime = path('/run/modelone')
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    authorized_keys = runtime / 'authorized_keys'
    if keys_file:
        keys = path(keys_file).read_text()
        if not keys.strip():
            raise ValueError('Notebook SSH public key file is empty')
        authorized_keys.write_text(keys.rstrip() + '\n')
        authorized_keys.chmod(0o600)
        command('ssh-keygen', '-l', '-f', str(authorized_keys), stdout=subprocess.DEVNULL)
    elif authorized_keys.exists():
        authorized_keys.unlink()

    # Unlock root for public-key authentication without a reusable password.
    # chpasswd reads stdin, so secrets never enter command arguments or logs.
    command('chpasswd', input='root:' + (password or secrets.token_urlsafe(48)) + '\n', text=True)
    config.write_text('\n'.join([
        f'Port {port}', 'PermitEmptyPasswords no', 'KbdInteractiveAuthentication no',
        'UsePAM yes', 'AllowUsers root', 'StrictModes yes',
        'PermitRootLogin ' + ('yes' if password else 'prohibit-password'),
        'PasswordAuthentication ' + ('yes' if password else 'no'),
        'PubkeyAuthentication ' + ('yes' if keys_file else 'no'),
        'AuthorizedKeysFile /run/modelone/authorized_keys',
        'Subsystem sftp internal-sftp', '',
    ]))
    path('/run/sshd').mkdir(parents=True, exist_ok=True)
    command('ssh-keygen', '-A')
    command('/usr/sbin/sshd', '-t')
    command('service', 'ssh', 'start')
    print('Notebook SSH enabled with per-notebook credentials')


if __name__ == '__main__':
    try:
        initialize(os.environ)
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        # Do not include process input or environment values in diagnostics.
        print('Notebook initialization failed (' + type(error).__name__ + '). '
              'Check credential files, port and filesystem permissions.', file=sys.stderr)
        sys.exit(1)
