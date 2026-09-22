#!/usr/bin/env python3
"""Smoke-test a built backend, optionally through a frontend proxy, on Docker.

Uses only cached images; publishes a random loopback port and cleans up its
containers, temporary data and network. Does not run Kubernetes workloads.
"""
import argparse
import hashlib
import importlib.util
import ipaddress
import json
import secrets
import ssl
import subprocess
import tempfile
import time
from pathlib import Path
from http.cookiejar import CookieJar
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen, build_opener, HTTPCookieProcessor, HTTPRedirectHandler, HTTPSHandler, Request
from datetime import datetime, timezone
from brand_scan import OLD, HOSTS, TECHNICAL
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


def check_business_apis(expect, browser, sql, report):
    """Read fresh-install page APIs; never follow action/deployment links.

    Some serializers consult Kubernetes for live resources. The isolated fresh
    database must contain no online resources before we read these lists. Mark
    the unstarted sample notebook offline in this temporary database only.
    Response bodies (which may contain tokens) stay in memory.
    """
    if sql("SELECT COUNT(*) FROM inferenceservice WHERE model_status='online'") != '0':
        raise AssertionError('Business API smoke requires an idle fresh database')
    sql("UPDATE notebook SET expand=JSON_SET(COALESCE(NULLIF(expand,''),'{}'), '$.status', 'offline')")
    report['businessFixtures'] = 'Fresh-install sample notebooks marked offline in the temporary database to avoid Kubernetes status lookup; no resources deployed.'

    def check_brand(value, location):
        if isinstance(value, dict):
            for key, item in value.items():
                check_brand(item, location + '.' + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                check_brand(item, location + '[' + str(index) + ']')
        elif isinstance(value, str):
            safe = value
            for pattern in TECHNICAL:
                safe = pattern.sub('', safe)
            if HOSTS.search(value) or OLD.search(safe):
                # Include only a field location, never a credential-bearing body.
                raise AssertionError('Legacy brand/resource in ' + location)

    def fetch(path):
        _, headers, body = expect(path, 200, browser=browser)
        if headers.get_content_type() != 'application/json':
            raise AssertionError('Expected JSON from ' + path.split('?')[0])
        payload = json.loads(body)
        if isinstance(payload, dict) and payload.get('status', 0) != 0:
            raise AssertionError('Nonzero application status from ' + path.split('?')[0])
        check_brand(payload, path.split('?')[0])
        return payload

    def row_ids(rows, primary_key):
        if not isinstance(rows, list):
            raise AssertionError('List rows are missing')
        ids = []
        for row in rows:
            if not isinstance(row, dict) or primary_key not in row:
                raise AssertionError('List row lacks its primary key')
            ids.append(row[primary_key])
            ids.extend(row_ids(row.get('children', []), primary_key))
        return ids

    # Only reviewed read endpoints: no arbitrary URLs from server responses.
    endpoints = [
        ('Projects', '/project_modelview/api/', True),
        ('Project groups', '/project_modelview/org/api/', True),
        ('Notebook', '/notebook_modelview/api/', True),
        ('Pipeline', '/pipeline_modelview/api/', True),
        ('Pipeline home', '/pipeline_modelview/home/api/', True),
        ('Task templates', '/job_template_modelview/api/', True),
        ('Training models', '/training_model_modelview/api/', True),
        ('Training model page', '/training_model_modelview/web/api/', True),
        ('Inference', '/inferenceservice_modelview/api/', True),
        ('AIHub', '/model_market/all/api/', True),
        ('AIHub visual', '/model_market/visual/api/', False),
        ('AIHub voice', '/model_market/voice/api/', False),
        ('AIHub language', '/model_market/language/api/', False),
        ('AIHub multimodal', '/model_market/multimodal/api/', False),
        ('AIHub generative', '/model_market/aigc/api/', False),
        ('Datasets', '/dataset_modelview/api/', True),
        ('Chat configuration', '/chat_modelview/api/', True),
        ('Chat sessions', '/aitalk_modelview/api/', True),
        ('ETL', '/etl_pipeline_modelview/api/', True),
        ('AutoML', '/nni_modelview/api/', True),
    ]
    results = report['businessApis'] = []
    failures = []
    for label, base, seeded in endpoints:
        result = {'module': label, 'base': base}
        results.append(result)
        try:
            info = fetch(base + '_info')
            if (not isinstance(info, dict) or info.get('route_base') != base
                    or not isinstance(info.get('list_columns'), list) or not info['list_columns']
                    or not isinstance(info.get('label_columns'), dict)
                    or not info.get('primary_key')):
                raise AssertionError('Missing or inconsistent page metadata')
            # The generic project API feeds a selector and has no page title.
            if base != '/project_modelview/api/' and not info.get('list_title'):
                raise AssertionError('Missing page title')
            all_ids, page, count = [], 0, None
            while True:
                payload = fetch(base + '?' + urlencode({'form_data': json.dumps({
                    'page': page, 'page_size': 20, 'str_related': 1})}))
                if not isinstance(payload, dict) or payload.get('status') != 0:
                    raise AssertionError('Missing list success status')
                data = payload.get('result')
                if not isinstance(data, dict) or type(data.get('count')) is not int:
                    raise AssertionError('Missing list count')
                if count is None:
                    count = data['count']
                    if count < (1 if seeded else 0):
                        raise AssertionError('Expected initialized records')
                elif count != data['count']:
                    raise AssertionError('Unstable list count')
                ids = row_ids(data.get('data'), info['primary_key'])
                all_ids.extend(ids)
                if len(all_ids) >= count:
                    break
                if not ids or page >= 100:
                    raise AssertionError('Pagination did not reach the declared count')
                page += 1
            if len(all_ids) != count or len(set(all_ids)) != count:
                raise AssertionError('Pagination omitted or repeated initialized records')
            result.update(status='passed', records=count, pages=page + 1)
        except (AssertionError, ValueError, KeyError, TypeError) as error:
            result.update(status='failed', error=str(error))
            failures.append(label)
    for path in ['/myapp/menu', '/myapp/navbar_right', '/myapp/navbar_left', '/myapp/navbar_bottom',
                 '/pipeline_modelview/api/my/list/', '/pipeline_modelview/api/demo/list/']:
        result = {'path': path}
        results.append(result)
        try:
            payload = fetch(path)
            rows = payload.get('result') if isinstance(payload, dict) else payload
            if not isinstance(rows, list):
                raise AssertionError('Expected navigation or pipeline list')
            if path.endswith(('/my/list/', '/demo/list/')) and not rows:
                raise AssertionError('Expected initialized pipeline shortcuts')
            result.update(status='passed', records=len(rows))
        except (AssertionError, ValueError, KeyError, TypeError) as error:
            result.update(status='failed', error=str(error))
            failures.append(path)
    if failures:
        raise AssertionError('Business API validation failed: ' + ', '.join(failures))
    report['checks'].append('authenticated business lists, full pagination, initialized records, page metadata and navigation pass runtime brand checks; no workloads started')


def run_smoke(args):
    prefix = 'modelone-app-test-' + secrets.token_hex(5)
    password = secrets.token_urlsafe(24)
    redis_password = secrets.token_urlsafe(32)
    credentials = {name: secrets.token_urlsafe(48) for name in
                   ('MODELONE_SECRET_KEY', 'MODELONE_JWT_KEY', 'MODELONE_ADMIN_PASSWORD')}
    private_values = [password, redis_password, *credentials.values()]

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
    images = [args.backend_image, args.mysql_image, args.redis_image]
    if args.frontend_image:
        images.append(args.frontend_image)
        report['scope'] = 'Local Docker fresh-install and HTTP smoke test through the frontend Nginx proxy; no browser, TLS gateway or cluster business jobs.'
    if args.https:
        report['scope'] = 'Local Docker production Gunicorn, frontend proxy and HTTPS gateway using a temporary trusted certificate; no enterprise TLS, browser, SSO or cluster business jobs.'
    if args.nginx_config:
        report['nginxConfigSha256'] = hashlib.sha256(args.nginx_config.read_bytes()).hexdigest()
    report['images'] = {image: run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}']).stdout.strip() for image in images}
    with tempfile.TemporaryDirectory(prefix='modelone-app-') as td:
        folder = Path(td)
        mysqlenv = folder / 'mysql.env'
        mysqlenv.write_text('MYSQL_ROOT_PASSWORD=' + password + '\nMYSQL_ROOT_HOST=%\n')
        mysqlenv.chmod(384)
        appenv = folder / 'app.env'
        stage = 'prod' if args.https else 'dev'
        appenv.write_text('STAGE=' + stage + '\nENVIRONMENT=DEV\nMYSQL_SERVICE=mysql+pymysql://root:' + password + '@db:3306/kubeflow?charset=utf8mb4\nREDIS_HOST=redis\nREDIS_PORT=6379\nREDIS_PASSWORD=' + redis_password + '\nMODELONE_COPYRIGHT_HOLDER=Validation Company\nMODELONE_TITLE=modelOne Runtime Validation\nMODELONE_PRIMARY_COLOR=#123456\n' + ''.join(k + '=' + v + '\n' for k, v in credentials.items()))
        appenv.chmod(384)
        run(['docker', 'network', 'create', '--label', 'modelone.validation=true', prefix])
        try:
            frontend_network = []
            tls_context = None
            if args.https:
                subnet = json.loads(run(['docker', 'network', 'inspect', prefix]).stdout)[0]['IPAM']['Config'][0]['Subnet']
                # Docker only allows a fixed endpoint on an explicitly configured
                # subnet. Reuse its just-allocated unused subnet before starting peers.
                run(['docker', 'network', 'rm', prefix])
                run(['docker', 'network', 'create', '--label', 'modelone.validation=true', '--subnet', subnet, prefix])
                frontend_ip = str(ipaddress.ip_network(subnet)[10])
                frontend_network = ['--ip', frontend_ip]
                with appenv.open('a') as env_file:
                    env_file.write('MODELONE_WEB_WORKERS=1\nMODELONE_TRUSTED_PROXY_IPS=' + frontend_ip + '\n')
            for role, image, extras in [('db', args.mysql_image, ['--env-file', str(mysqlenv), '--tmpfs', '/var/lib/mysql:rw,size=1g']), ('redis', args.redis_image, ['--env', 'REDIS_PASSWORD=' + redis_password])]:
                name = prefix + '-' + role
                containers.append(name)
                run(['docker', 'run', '-d', '--pull', 'never', '--name', name, '--network', prefix, '--network-alias', role, '--label', 'modelone.validation=true', *extras, image])
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                result = run(['docker', 'exec', prefix + '-db', 'sh', '-c', 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --silent --execute="SELECT 1"'], False)
                if result.returncode == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError('mysql did not become ready')
            for attempt in range(30):
                if run(['docker', 'exec', prefix + '-redis', 'redis-cli', '-a', redis_password, 'ping'], False).stdout.strip() == 'PONG':
                    break
                time.sleep(1)
            else:
                raise RuntimeError('redis did not become ready')
            print('Isolated MySQL and Redis ready', flush=True)
            app = prefix + '-myapp'
            containers.append(app)
            run(['docker', 'run', '-d', '--pull', 'never', '--platform', 'linux/amd64', '--name', app, '--network', prefix, '--network-alias', 'myapp', '--network-alias', 'kubeflow-dashboard.infra', '--label', 'modelone.validation=true', '--env-file', str(appenv), '--tmpfs', '/data/k8s/kubeflow:rw,size=512m', '--publish', '127.0.0.1::80', args.backend_image, 'bash', '/entrypoint.sh'])
            port = run(['docker', 'inspect', app, '--format', '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}']).stdout.strip()
            origin = 'http://127.0.0.1:' + port
            backend_origin = origin
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
            if args.https and 'gunicorn' not in run(['docker', 'exec', app, 'cat', '/proc/1/cmdline']).stdout:
                raise AssertionError('HTTPS validation must use the production Gunicorn process')
            if args.frontend_image:
                frontend = prefix + '-frontend'
                config_mount = []
                if args.nginx_config:
                    config_mount = ['--mount', 'type=bind,source=%s,target=/etc/nginx/conf.d/default.conf,readonly'
                                    % args.nginx_config.resolve()]
                containers.append(frontend)
                run(['docker', 'run', '-d', '--pull', 'never', '--name', frontend, '--network', prefix,
                     '--network-alias', 'frontend', *frontend_network,
                     '--label', 'modelone.validation=true', '--publish', '127.0.0.1::80',
                     *config_mount, args.frontend_image])
                port = run(['docker', 'inspect', frontend, '--format', '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}']).stdout.strip()
                origin = 'http://127.0.0.1:' + port
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    try:
                        with urlopen(origin + '/health', timeout=3) as response:
                            if response.status == 200:
                                break
                    except (OSError, HTTPError):
                        time.sleep(0.5)
                else:
                    raise RuntimeError('Frontend proxy health timeout')
                print('Frontend proxy ready; all HTTP checks use the shared entrypoint', flush=True)
            if args.https:
                # The temporary trust is local to this test process; system and
                # browser certificate stores are not modified.
                cert_config = folder / 'tls.cnf'
                tls_dir = folder / 'tls'
                tls_dir.mkdir()
                cert_config.write_text('[req]\ndistinguished_name=subject\nx509_extensions=extensions\nprompt=no\n'
                                       '[subject]\nCN=127.0.0.1\n[extensions]\nsubjectAltName=IP:127.0.0.1\n'
                                       'basicConstraints=critical,CA:TRUE\nkeyUsage=critical,digitalSignature,keyEncipherment,keyCertSign\n'
                                       'extendedKeyUsage=serverAuth\n')
                run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
                     '-config', str(cert_config), '-keyout', str(tls_dir / 'tls.key'), '-out', str(tls_dir / 'tls.crt')])
                (tls_dir / 'tls.key').chmod(384)
                tls_context = ssl.create_default_context(cafile=str(tls_dir / 'tls.crt'))
                gateway_config = folder / 'gateway.conf'
                gateway_config.write_text('''server {
    listen 443 ssl;
    ssl_certificate /test-tls/tls.crt;
    ssl_certificate_key /test-tls/tls.key;
    location / {
        proxy_pass http://frontend:80;
        proxy_set_header Host $http_host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Protocol "";
        proxy_set_header X-Forwarded-Ssl "";
    }
}''')
                gateway = prefix + '-gateway'
                containers.append(gateway)
                run(['docker', 'run', '-d', '--pull', 'never', '--name', gateway, '--network', prefix,
                     '--label', 'modelone.validation=true', '--publish', '127.0.0.1::443',
                     '--mount', 'type=bind,source=%s,target=/test-tls,readonly' % tls_dir,
                     '--mount', 'type=bind,source=%s,target=/etc/nginx/conf.d/default.conf,readonly' % gateway_config,
                     args.frontend_image])
                port = run(['docker', 'inspect', gateway, '--format', '{{(index (index .NetworkSettings.Ports "443/tcp") 0).HostPort}}']).stdout.strip()
                origin = 'https://127.0.0.1:' + port
                deadline = time.monotonic() + 30
                while time.monotonic() < deadline:
                    try:
                        with urlopen(origin + '/health', context=tls_context, timeout=3) as response:
                            if response.status == 200:
                                break
                    except OSError:
                        time.sleep(0.5)
                else:
                    raise RuntimeError('TLS gateway health timeout')
                try:
                    with urlopen(origin + '/health', timeout=3):
                        raise AssertionError('Temporary certificate was accepted without test-specific trust')
                except URLError as error:
                    if not isinstance(error.reason, ssl.SSLCertVerificationError):
                        raise
                report['checks'].append('HTTPS certificate accepted only with isolated test trust; production Gunicorn trusts only the frontend proxy IP')
                print('HTTPS gateway ready with certificate verification and production cookies', flush=True)
            revision = run(['docker', 'exec', prefix + '-db', 'sh', '-c', 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --batch --skip-column-names --execute="SELECT version_num FROM kubeflow.alembic_version"']).stdout.strip()
            if revision != 'modelone_brand_links_20260921':
                raise AssertionError('Unexpected migration revision: ' + revision)
            report['checks'].append('fresh database initialized to latest migration and /health=200')
            for path in ['/login/', '/myapp/brand.js', '/static/assets/modelone/modelone-mark.svg']:
                with urlopen(origin + path, context=tls_context, timeout=15) as r:
                    text = r.read().decode()
                    if 'modelOne' not in text or 'cube-studio' in text.lower():
                        raise AssertionError('Unexpected brand response: ' + path)
                    if path == '/login/' and ('login-card' not in text or 'modelone-logo.svg' not in text):
                        raise AssertionError('Login response did not use the modelOne branded template')
                    report['checks'].append(path + (' uses the branded login template' if path == '/login/' else ' has modelOne brand'))
            for app_name, scope in (('frontend', '/frontend/'), ('vision', '/static/appbuilder/vison/'),
                                    ('visionPlus', '/static/appbuilder/visonPlus/')):
                with urlopen(origin + '/myapp/manifest/' + app_name + '.json', context=tls_context, timeout=15) as r:
                    manifest = json.load(r)
                    if r.headers.get_content_type() != 'application/manifest+json' or r.headers.get('Cache-Control') != 'no-store':
                        raise AssertionError('Runtime manifest response headers are incorrect')
                    if (manifest['name'] != 'modelOne Runtime Validation' or manifest['theme_color'] != '#123456'
                            or manifest['scope'] != scope or manifest['start_url'] != scope):
                        raise AssertionError('Runtime manifest did not use deployment overrides: ' + app_name)
            report['checks'].append('three public PWA manifests use runtime branding, app scopes and no-store caching')
            print('Fresh database initialized; checking authentication', flush=True)

            def client():
                return build_opener(HTTPSHandler(context=tls_context), HTTPCookieProcessor(CookieJar()), NoRedirect())

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

            def expect_error_page(status, browser=None):
                page = expect('/modelone-validation-missing', status, browser=browser)[2]
                if ('modelOne Runtime Validation' not in page or 'modelone-logo.svg' not in page
                        or 'cube-studio' in page.lower()):
                    raise AssertionError('Missing runtime brand on error page: ' + str(status))

            def sql(statement):
                return run(['docker', 'exec', prefix + '-db', 'sh', '-c',
                            'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --host=127.0.0.1 --user=root --batch --skip-column-names kubeflow --execute="$1"', 'sql', statement]).stdout.strip()

            expect('/myapp/manifest/unknown.json', 404)
            if args.frontend_image:
                if expect('/', 301)[1].get('Location') != '/frontend/':
                    raise AssertionError('Unexpected shared entrypoint redirect')
                for base in ('/frontend/', '/static/appbuilder/vison/', '/static/appbuilder/visonPlus/'):
                    page = expect(base, 200)[2]
                    if '<title>modelOne' not in page or 'data-modelone-app=' not in page:
                        raise AssertionError('Missing branded frontend: ' + base)
                report['checks'].append('shared entrypoint serves three product apps and proxies health, login and runtime branding')

            protected = '/project_modelview/api/'
            browser = client()
            expect('/login/?username=admin', 200, browser=browser)
            expect(protected, 401, browser=browser)
            expect_error_page(401, browser)
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
                return http('/login/' + query, browser=browser, data=urlencode(fields).encode(),
                            headers={'Referer': origin + '/login/', 'Origin': origin})

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
            expect_error_page(404, browser)
            report['checks'].append('unauthenticated and missing-page HTML responses use the deployed modelOne brand')
            cookie = next((value for value in result[1].get_all('Set-Cookie', []) if value.startswith('session=')), '')
            if 'HttpOnly' not in cookie or 'SameSite=Lax' not in cookie:
                raise AssertionError('Session cookie flags missing')
            if args.https and 'Secure' not in cookie:
                raise AssertionError('Production session cookie is not Secure')
            print('Password session established; checking business page APIs', flush=True)
            check_business_apis(expect, browser, sql, report)
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
            if args.https:
                # Untrusted direct peers cannot spoof a secure request using
                # forwarding headers. The TLS gateway also replaces client values.
                spoofed = Request(backend_origin + '/login/api/', data=body, headers={
                    'Content-Type': 'application/json', 'Origin': backend_origin.replace('http:', 'https:'),
                    'X-Forwarded-Proto': 'https'})
                try:
                    response = client().open(spoofed, timeout=20)
                except HTTPError as error:
                    response = error
                with response:
                    if response.status != 401:
                        raise AssertionError('Backend trusted a forwarding header from a direct client')
                expect('/login/api/', 200, browser=client(), data=body, headers={
                    'Content-Type': 'application/json', 'Origin': origin, 'X-Forwarded-Proto': 'http',
                    'X-Forwarded-Protocol': 'http', 'X-Forwarded-Ssl': 'off'})
                report['checks'].append('Secure cookies and HTTPS same-origin login work; direct forwarding spoof denied and gateway overwrites client scheme headers')
            for supplied_origin in ('https://example.invalid', 'null'):
                foreign_browser = client()
                expect('/login/api/', 401, browser=foreign_browser,
                       headers={'Content-Type': 'application/json', 'Origin': supplied_origin}, data=body)
                expect(protected, 401, browser=foreign_browser)
            same_origin_browser = client()
            expect('/login/api/', 200, browser=same_origin_browser,
                   headers={'Content-Type': 'application/json', 'Origin': origin}, data=body)
            expect(protected, 200, browser=same_origin_browser)
            expect('/login/api/', 200, browser=browser, headers={'Content-Type': 'application/json'}, data=body)
            expect(protected, 200, browser=browser)
            report['checks'].append('short/full/Bearer API tokens and same-origin login accepted; expired/incorrect signatures, foreign and null login origins denied without a session')

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
            for name in reversed(containers):
                if run(['docker', 'container', 'inspect', name], False).returncode:
                    continue
                if name.endswith(('-myapp', '-frontend', '-gateway')):
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
    parser.add_argument('--frontend-image', help='Run all HTTP checks through this cached frontend image')
    parser.add_argument('--nginx-config', type=Path, help='Mount a deployment Nginx configuration; requires --frontend-image')
    parser.add_argument('--https', action='store_true', help='Use production Gunicorn and an isolated HTTPS gateway; requires --frontend-image and openssl')
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/modelone')
    args = parser.parse_args()
    if args.nginx_config and not args.frontend_image:
        parser.error('--nginx-config requires --frontend-image')
    if args.https and not args.frontend_image:
        parser.error('--https requires --frontend-image')
    run_smoke(args)
