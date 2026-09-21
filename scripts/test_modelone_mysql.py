#!/usr/bin/env python3
"""Exercise brand migration and backup/restore on an isolated disposable MySQL.

Requires Docker, SQLAlchemy, PyMySQL, mysql and mysqldump. Uses only a local
cached image (--pull never), a temporary database volume and a loopback port.
No existing containers, databases, networks or credentials are reused.
"""
import argparse
import importlib.util
import json
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'myapp' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def command(args, expected=0):
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode != expected:
        raise RuntimeError('%s failed (%s): %s' % (args[0], result.returncode, result.stderr.strip()))
    return result.stdout


def check(condition, message):
    if not condition:
        raise AssertionError(message)


def snapshot(connection):
    return {name: [dict(row) for row in connection.execute(sa.text('SELECT * FROM ' + name + ' ORDER BY id')).mappings()]
            for name in ('chat', 'images', 'pipeline', 'dataset')}


def run(args):
    for executable in ('docker', 'mysql', 'mysqldump'):
        if not shutil.which(executable):
            raise RuntimeError('Required executable not found: ' + executable)
    image_id = command(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}}']).strip()
    token = secrets.token_hex(6)
    container = 'modelone-mysql-test-' + token
    network = container + '-net'
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'mysqlImage': args.image,
              'imageId': image_id, 'checks': [], 'scope': 'Isolated fixture database; not a full application install or production upgrade.'}
    engines = []
    network_created = False
    container_created = False

    def passed(name):
        report['checks'].append(name)
        print('PASS: ' + name, flush=True)

    with tempfile.TemporaryDirectory(prefix='modelone-mysql-') as folder:
        folder = Path(folder)
        password = secrets.token_urlsafe(32)
        secret = folder / 'mysql.env'
        secret.write_text('MYSQL_ROOT_PASSWORD=%s\nMYSQL_ROOT_HOST=%%\n' % password)
        secret.chmod(0o600)
        try:
            command(['docker', 'network', 'create', '--label', 'modelone.validation=true', network])
            network_created = True
            command(['docker', 'run', '--detach', '--pull', 'never', '--name', container,
                     '--network', network, '--label', 'modelone.validation=true',
                     '--publish', '127.0.0.1::3306', '--tmpfs', '/var/lib/mysql:rw,size=1g',
                     '--env-file', str(secret), args.image,
                     '--default-authentication-plugin=mysql_native_password'])
            container_created = True
            port = int(command(['docker', 'inspect', container, '--format',
                                '{{(index (index .NetworkSettings.Ports "3306/tcp") 0).HostPort}}']).strip())
            url = sa.engine.URL.create('mysql+pymysql', username='root', password=password,
                                       host='127.0.0.1', port=port, query={'charset': 'utf8mb4'})
            admin = sa.create_engine(url, connect_args={'connect_timeout': 2})
            engines.append(admin)
            deadline = time.monotonic() + 120
            print('Waiting for isolated MySQL on loopback...', flush=True)
            while True:
                try:
                    with admin.connect() as connection:
                        report['serverVersion'] = connection.execute(sa.text('SELECT VERSION()')).scalar()
                    break
                except sa.exc.OperationalError:
                    if time.monotonic() > deadline:
                        raise RuntimeError('Disposable MySQL did not become ready within 120 seconds') from None
                    state = command(['docker', 'inspect', container, '--format', '{{.State.Running}}']).strip()
                    if state != 'true':
                        raise RuntimeError('Disposable MySQL stopped during initialization')
                    time.sleep(1)
            client_config = folder / 'mysql-client.cnf'
            client_config.write_text('[client]\nuser=root\npassword=%s\nhost=127.0.0.1\nport=%s\nprotocol=tcp\n' % (password, port))
            client_config.chmod(0o600)
            with admin.begin() as connection:
                for name in ('modelone_before', 'modelone_restore', 'modelone_empty'):
                    connection.execute(sa.text('CREATE DATABASE ' + name + ' CHARACTER SET utf8mb4'))
            before = sa.create_engine(url.set(database='modelone_before'))
            restored = sa.create_engine(url.set(database='modelone_restore'))
            empty = sa.create_engine(url.set(database='modelone_empty'))
            engines.extend((before, restored, empty))
            brand = load('brand')
            brand.BRAND.update(image_registry='registry.example.test/team', asset_base_url='https://assets.example.test', help_url='https://help.example.test')
            migration = load('brand_migration')
            with empty.begin() as connection:
                check(migration.migrate_connection(connection, brand.BRAND, brand.resolve_resources) == 0, 'Empty optional modules should be skipped')
            passed('migration tolerates a fresh database with no optional tables')
            with before.begin() as connection:
                connection.execute(sa.text('CREATE TABLE chat (id INT PRIMARY KEY, name VARCHAR(200) UNIQUE, label VARCHAR(200), hello TEXT, tips TEXT, prompt TEXT, knowledge TEXT)'))
                connection.execute(sa.text('CREATE TABLE images (id INT PRIMARY KEY, name VARCHAR(500), gitpath VARCHAR(500))'))
                connection.execute(sa.text('CREATE TABLE pipeline (id INT PRIMARY KEY, name VARCHAR(100), parameter TEXT)'))
                connection.execute(sa.text('CREATE TABLE dataset (id INT PRIMARY KEY, name VARCHAR(200), source VARCHAR(200), icon TEXT)'))
                connection.execute(sa.text('INSERT INTO chat VALUES (1, :name, :label, NULL, :tips, :prompt, :knowledge)'),
                                   {'name': 'cube-studio', 'label': 'CubeStudio 平台', 'tips': '["如何使用 Cube Studio？"]',
                                    'prompt': '{{history}}\nHuman:{{query}}\nAI:', 'knowledge': '{"file":"/mnt/admin/pipeline/example/gpt/cube-studio.csv"}'})
                connection.execute(sa.text('INSERT INTO images VALUES (1, :image, :gitpath)'),
                                   {'image': 'ccr.ccs.tencentyun.com/cube-studio/notebook:v1', 'gitpath': 'https://github.com/data-infra/cube-studio/tree/main/images'})
                connection.execute(sa.text('INSERT INTO pipeline VALUES (1, :name, :parameter)'),
                                   {'name': 'cube-studio-job', 'parameter': '{"img":"https://cube-studio.oss-cn-hangzhou.aliyuncs.com/demo.png"}'})
                connection.execute(sa.text('INSERT INTO dataset VALUES (1, :name, :source, :icon)'),
                                   {'name': 'cube-studio-data', 'source': 'cube_studio', 'icon': 'https://cube-studio.oss-cn-hangzhou.aliyuncs.com/dataset.png'})
                original = snapshot(connection)
            backup = folder / 'before.sql'
            common = ['--client-config', str(client_config)]
            backup_cmd = [sys.executable, str(ROOT / 'scripts/backup_modelone.py'), *common, '--database', 'modelone_before', '--output', str(backup)]
            command(backup_cmd)
            check(backup.stat().st_mode & 0o077 == 0, 'Backup permissions must be private')
            passed('mysqldump backup with protected credentials and checksum')
            with before.begin() as connection:
                check(migration.migrate_connection(connection, brand.BRAND, brand.resolve_resources) == 4, 'Expected all four legacy records to change')
                changed = snapshot(connection)
                check(changed['chat'][0]['name'] == original['chat'][0]['name'], 'Chat URL identity changed')
                check(changed['pipeline'][0]['name'] == original['pipeline'][0]['name'], 'Pipeline identity changed')
                check(changed['chat'][0]['prompt'] == original['chat'][0]['prompt'], 'Prompt placeholders changed')
                check(changed['chat'][0]['hello'] is None, 'NULL welcome text changed')
                check(changed['chat'][0]['label'] == 'modelOne 平台', 'Visible brand not migrated')
                check(json.loads(changed['chat'][0]['tips']) == ['如何使用 modelOne？'], 'JSON display text not migrated')
                check(changed['images'][0]['gitpath'] == 'https://help.example.test', 'Documentation link not migrated')
                check(changed['images'][0]['name'] == 'registry.example.test/team/modelone/notebook:v1', 'Image registry not migrated')
                check(json.loads(changed['pipeline'][0]['parameter'])['img'] == 'https://assets.example.test/demo.png', 'Preview resource not migrated')
                check(changed['dataset'][0]['source'] == 'modelOne', 'Dataset producer not migrated')
                check(migration.migrate_connection(connection, brand.BRAND, brand.resolve_resources) == 0, 'Migration is not idempotent')
            passed('MySQL brand migration preserves identifiers and JSON and is idempotent')
            restore_cmd = [sys.executable, str(ROOT / 'scripts/restore_modelone.py'), *common, '--database', 'modelone_restore', '--backup', str(backup)]
            command(restore_cmd)
            with restored.connect() as connection:
                check(not sa.inspect(connection).get_table_names(), 'Restore preview must not write data')
            command(restore_cmd + ['--apply'])
            with restored.connect() as connection:
                check(snapshot(connection) == original, 'Restored metadata differs from the original backup')
            passed('restore preview is read-only and applied restore exactly recovers original metadata')
            check('non-empty database' in subprocess.run(restore_cmd + ['--apply'], capture_output=True, text=True).stderr, 'Non-empty restore was not rejected')
            backup.write_bytes(backup.read_bytes() + b'\n-- tampered\n')
            check('checksum does not match' in subprocess.run(restore_cmd, capture_output=True, text=True).stderr, 'Corrupt backup was not rejected')
            passed('restore rejects non-empty databases and corrupted backups')
            report['status'] = 'passed'
        except Exception as error:
            report['status'] = 'failed'
            report['error'] = str(error).replace(password, '[redacted]')
            raise
        finally:
            for engine in engines:
                engine.dispose()
            if container_created:
                command(['docker', 'rm', '--force', '--volumes', container])
            if network_created:
                command(['docker', 'network', 'rm', network])
            report['finishedAt'] = datetime.now(timezone.utc).isoformat()
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('Validation report: ' + str(args.report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', default='mysql:8.0.32', help='locally cached MySQL 8.0 image; never pulled automatically')
    parser.add_argument('--report', type=Path, default=ROOT / 'dist/modelone/mysql-validation.json')
    arguments = parser.parse_args()
    run(arguments)
