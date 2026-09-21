#!/usr/bin/env python3
"""Smoke-test a built backend with disposable MySQL and Redis on Docker.

Uses only cached images; publishes a random loopback port and cleans up its
containers, temporary data and network. Does not run Kubernetes workloads.
"""
import argparse
import importlib.util
import json
import secrets
import subprocess
import tempfile
import time
from pathlib import Path
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, HTTPCookieProcessor, HTTPRedirectHandler, Request
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1]

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Inputs(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'input' and attrs.get('name'):
            self.values[attrs['name']] = attrs.get('value', '')


def run_smoke(args):
    prefix = 'modelone-app-test-' + secrets.token_hex(5)
    password = secrets.token_urlsafe(24)
    credentials = {name: secrets.token_urlsafe(48) for name in
                   ('MODELONE_SECRET_KEY', 'MODELONE_JWT_KEY', 'MODELONE_ADMIN_PASSWORD')}
    private_values = [password, *credentials.values()]

    def redact(value):
        for secret in private_values:
            value = value.replace(secret, '[redacted]')
        return value

    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'checks': [], 'scope': 'Local Docker fresh-install and HTTP smoke test using cached base images; no cluster business jobs.'}
    containers = []

    def run(args, check=True):
        r = subprocess.run(args, capture_output=True, text=True)
        if check and r.returncode:
            raise RuntimeError(redact(r.stderr)[-3000:])
        return r
    report['images'] = {image: run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}']).stdout.strip() for image in (args.backend_image, args.mysql_image, args.redis_image)}
    with tempfile.TemporaryDirectory(prefix='modelone-app-') as td:
        folder = Path(td)
        mysqlenv = folder / 'mysql.env'
        mysqlenv.write_text('MYSQL_ROOT_PASSWORD=' + password + '\nMYSQL_ROOT_HOST=%\n')
        mysqlenv.chmod(384)
        appenv = folder / 'app.env'
        appenv.write_text('STAGE=dev\nENVIRONMENT=DEV\nMYSQL_SERVICE=mysql+pymysql://root:' + password + '@db:3306/kubeflow?charset=utf8mb4\nREDIS_HOST=redis\nREDIS_PORT=6379\nREDIS_PASSWORD=\nMODELONE_COPYRIGHT_HOLDER=Validation Company\n' + ''.join(k + '=' + v + '\n' for k, v in credentials.items()))
        appenv.chmod(384)
        run(['docker', 'network', 'create', '--label', 'modelone.validation=true', prefix])
        try:
            for role, image, extras in [('db', args.mysql_image, ['--env-file', str(mysqlenv), '--tmpfs', '/var/lib/mysql:rw,size=1g']), ('redis', args.redis_image, ['--env', 'ALLOW_EMPTY_PASSWORD=yes'])]:
                name = prefix + '-' + role
                run(['docker', 'run', '-d', '--pull', 'never', '--name', name, '--network', prefix, '--network-alias', role, '--label', 'modelone.validation=true', *extras, image])
                containers.append(name)
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                result = run(['docker', 'exec', prefix + '-db', 'sh', '-c', 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --silent --execute="SELECT 1"'], False)
                if result.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('mysql did not become ready')
            for attempt in range(30):
                if run(['docker', 'exec', prefix + '-redis', 'redis-cli', 'ping'], False).stdout.strip() == 'PONG':
                    break
                time.sleep(1)
            else:
                raise RuntimeError('redis did not become ready')
            print('Isolated MySQL and Redis ready', flush=True)
            app = prefix + '-myapp'
            run(['docker', 'run', '-d', '--pull', 'never', '--platform', 'linux/amd64', '--name', app, '--network', prefix, '--network-alias', 'myapp', '--label', 'modelone.validation=true', '--env-file', str(appenv), '--tmpfs', '/data/k8s/kubeflow:rw,size=512m', '--publish', '127.0.0.1::80', args.backend_image, 'bash', '/entrypoint.sh'])
            containers.append(app)
            port = run(['docker', 'inspect', app, '--format', '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}']).stdout.strip()
            origin = 'http://127.0.0.1:' + port
            deadline = time.monotonic() + 240
            while time.monotonic() < deadline:
                if run(['docker', 'inspect', app, '--format', '{{.State.Running}}']).stdout.strip() != 'true':
                    raise RuntimeError('Backend exited during initial setup')
                try:
                    with urlopen(origin + '/health', timeout=3) as r:
                        if r.status == 200:
                            break
                except Exception:
                    time.sleep(2)
            else:
                raise RuntimeError('Backend health timeout')
            revision = run(['docker', 'exec', prefix + '-db', 'sh', '-c', 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --batch --skip-column-names --execute="SELECT version_num FROM kubeflow.alembic_version"']).stdout.strip()
            if revision != 'modelone_brand_links_20260921':
                raise AssertionError('Unexpected migration revision: ' + revision)
            report['checks'].append('fresh database initialized to latest migration and /health=200')
            for path in ['/login/', '/myapp/brand.js', '/static/assets/modelone/modelone-mark.svg']:
                with urlopen(origin + path, timeout=15) as r:
                    text = r.read().decode()
                    if 'modelOne' not in text or 'cube-studio' in text.lower():
                        raise AssertionError('Unexpected brand response: ' + path)
                    report['checks'].append(path + ' has modelOne brand')
            print('Fresh database initialized; checking authentication', flush=True)

            def client():
                return build_opener(HTTPCookieProcessor(CookieJar()), NoRedirect())

            def http(path, browser=None, headers=None, data=None):
                req = Request(origin + path, headers=headers or {}, data=data)
                try:
                    response = (browser or client()).open(req, timeout=20)
                except HTTPError as error:
                    response = error
                with response:
                    return response.status, response.headers, response.read().decode()

            def expect(path, status, **kwargs):
                result = http(path, **kwargs)
                if result[0] != status:
                    raise AssertionError('%s: expected %d, got %d' % (path, status, result[0]))
                return result

            def sql(statement):
                return run(['docker', 'exec', prefix + '-db', 'sh', '-c',
                            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --batch --skip-column-names kubeflow --execute="$1"', 'sql', statement]).stdout.strip()

            protected = '/project_modelview/api/'
            browser = client()
            expect('/login/?username=admin', 200, browser=browser)
            expect(protected, 401, browser=browser)
            expect('/login/api/?token=admin', 401)
            for headers in ({'Authorization': 'admin'}, {'Authorization': 'admin', 'Host': 'kubeflow-dashboard.infra'}):
                expect(protected, 401, headers=headers)
            expect('/login/api/', 401, headers={'Content-Type': 'application/json'}, data=b'{"token":"admin"}')
            report['checks'].append('username login/query token/raw Authorization/spoofed Host denied')

            def password_login(username, supplied, browser, query=''):
                page = expect('/login/' + query, 200, browser=browser)[2]
                fields = Inputs(page).values
                if not fields.get('csrf_token'):
                    raise AssertionError('Login form has no CSRF token')
                fields.update(username=username, password=supplied)
                return http('/login/' + query, browser=browser, data=urlencode(fields).encode())

            before = sql('SELECT COUNT(*) FROM ab_user')
            for username, supplied in [('admin', 'wrong-password'), ('unregistered-operator', credentials['MODELONE_ADMIN_PASSWORD'])]:
                browser = client()
                if password_login(username, supplied, browser)[0] != 200:
                    raise AssertionError('Invalid password login unexpectedly redirected')
                expect(protected, 401, browser=browser)
            if sql('SELECT COUNT(*) FROM ab_user') != before:
                raise AssertionError('Unknown user was automatically registered')
            browser = client()
            expect('/login/', 200, browser=browser, data=urlencode({'username': 'admin', 'password': credentials['MODELONE_ADMIN_PASSWORD']}).encode())
            expect(protected, 401, browser=browser)
            report['checks'].append('wrong password, unknown account and missing CSRF denied; registration disabled')

            browser = client()
            result = password_login('admin', credentials['MODELONE_ADMIN_PASSWORD'], browser, '?login_url=https%3A%2F%2Fexample.invalid%2F')
            if result[0] != 302 or not result[1].get('Location', '').startswith('/'):
                raise AssertionError('Password login failed or accepted an external redirect')
            expect(protected, 200, browser=browser)
            cookie = next((value for value in result[1].get_all('Set-Cookie', []) if value.startswith('session=')), '')
            if 'HttpOnly' not in cookie or 'SameSite=Lax' not in cookie:
                raise AssertionError('Session cookie flags missing')
            expect('/logout', 302, browser=browser)
            expect(protected, 401, browser=browser)
            result = password_login('admin', credentials['MODELONE_ADMIN_PASSWORD'], client(), '?' + urlencode({'login_url': origin + protected}))
            if result[0] != 302 or result[1].get('Location') != protected:
                raise AssertionError('Same-origin login redirect not preserved')
            expect('/login/?login_url=http%3A%2F%2F%5B', 200)
            report['checks'].append('password login, safe redirect, session cookie flags and logout passed')

            spec = importlib.util.spec_from_file_location('auth_tokens', ROOT / 'myapp/auth_tokens.py')
            tokens = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tokens)
            token = tokens.issue_token('admin', credentials['MODELONE_JWT_KEY'])
            full = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.' + token
            private_values.extend([full, token])
            for value in (token, full, 'Bearer ' + full):
                expect(protected, 200, headers={'Authorization': value})
            malformed = tokens.jwt.encode({'sub': 'admin', 'iat': None, 'exp': None, 'iss': 'modelone', 'aud': 'modelone-api', 'scope': 'api'}, credentials['MODELONE_JWT_KEY'], algorithm='HS256')
            for value in (tokens.issue_token('admin', credentials['MODELONE_JWT_KEY'], ttl=-1), tokens.issue_token('admin', secrets.token_urlsafe(48)), malformed):
                private_values.append(value)
                expect(protected, 401, headers={'Authorization': value})
                expect('/login/api/', 401, headers={'Content-Type': 'application/json'}, data=json.dumps({'token': value}).encode())
            browser = client()
            body = json.dumps({'token': token}).encode()
            expect('/login/api/', 401, headers={'Content-Type': 'application/json', 'Origin': 'https://example.invalid'}, data=body)
            expect('/login/api/', 200, browser=browser, headers={'Content-Type': 'application/json'}, data=body)
            expect(protected, 200, browser=browser)
            report['checks'].append('short/full/Bearer API tokens accepted; expired/incorrect signatures and foreign login origin denied')

            task_token = tokens.issue_token('admin', credentials['MODELONE_JWT_KEY'], scope='task')
            private_values.append(task_token)
            expect(protected, 200, headers={'Authorization': task_token})
            expect('/users/list/', 401, headers={'Authorization': task_token})
            expect('/login/api/', 401, headers={'Content-Type': 'application/json'}, data=json.dumps({'token': task_token}).encode())
            report['checks'].append('task token accesses project API but cannot create a session or access users')

            sql("UPDATE ab_user SET active=0 WHERE username='admin'")
            expect(protected, 401, headers={'Authorization': token})
            expect(protected, 401, browser=browser)
            expect('/login/api/', 401, headers={'Content-Type': 'application/json'}, data=body)
            if password_login('admin', credentials['MODELONE_ADMIN_PASSWORD'], client())[0] != 200:
                raise AssertionError('Inactive account password login unexpectedly redirected')
            sql("UPDATE ab_user SET active=1 WHERE username='admin'")
            report['checks'].append('inactive account rejected for existing session, API token and password login')

            before = sql("SELECT password FROM ab_user WHERE username='admin'")
            run(['docker', 'exec', app, 'python', '-m', 'myapp.bootstrap_admin'])
            if before != sql("SELECT password FROM ab_user WHERE username='admin'"):
                raise AssertionError('Administrator password changed during bootstrap rerun')
            report['checks'].append('bootstrap rerun preserves existing administrator password')
            report['status'] = 'passed'
        except Exception as e:
            report['status'] = 'failed'
            report['error'] = redact(str(e))
        finally:
            logs = []
            cleanup_errors = []
            for name in containers:
                if name.endswith('-myapp'):
                    logs.append(run(['docker', 'logs', name], False).stdout + run(['docker', 'logs', name], False).stderr)
                if run(['docker', 'rm', '-f', '-v', name], False).returncode:
                    cleanup_errors.append(name)
            if run(['docker', 'network', 'rm', prefix], False).returncode:
                cleanup_errors.append(prefix)
            if cleanup_errors:
                report.update(status='failed', error='Failed to clean up: ' + ', '.join(cleanup_errors))
            if any(value in '\n'.join(logs) for value in private_values):
                report['status'] = 'failed'
                report['error'] = 'Generated authentication or database secret appeared in application logs'
            report['finishedAt'] = datetime.now(timezone.utc).isoformat()
            out = args.output
            out.mkdir(parents=True, exist_ok=True)
            (out / 'app-smoke-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            logpath = out / 'app-smoke.log'
            logpath.write_text(redact('\n'.join(logs)))
            logpath.chmod(384)
            print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
            if report['status'] == 'failed':
                print(logpath.read_text()[-6500:], flush=True)
                raise SystemExit(1)
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend-image', required=True)
    parser.add_argument('--mysql-image', default='mysql:8.0.32')
    parser.add_argument('--redis-image', required=True, help='Cached Bitnami-compatible Redis image')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/modelone')
    run_smoke(parser.parse_args())
