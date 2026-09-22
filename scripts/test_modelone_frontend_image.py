#!/usr/bin/env python3
"""Check real frontend HTTP responses from a locally built image on loopback.

Tests static delivery and proxy headers with a disposable Nginx echo upstream.
No application backend, registry, browser or cluster is used.
An intentionally mounted source map proves the web server denies publication.
"""
import argparse
import hashlib
from http.client import HTTPConnection, HTTPException
import json
import re
import secrets
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def command(args):
    return subprocess.check_output(args, text=True).strip()


def run(args):
    token = secrets.token_hex(6)
    container = 'modelone-web-test-' + token
    upstream = container + '-upstream'
    network = container + '-network'
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'image': args.image,
              'imageId': command(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}}']),
              'scope': 'Real Nginx static HTTP responses and proxy header transport; not a browser, TLS or authenticated backend test.', 'checks': []}
    if args.nginx_config:
        report['nginxConfigSha256'] = hashlib.sha256(args.nginx_config.read_bytes()).hexdigest()
    created = False
    upstream_created = False
    network_created = False
    with tempfile.TemporaryDirectory(prefix='modelone-web-test-') as folder:
        fixture = Path(folder) / 'blocked.js.map'
        fixture.write_text('{"sourcesContent":["must not be public"]}')
        echo_config = Path(folder) / 'upstream.conf'
        echo_config.write_text('''server {
    listen 80;
    location = /_modelone_proxy_probe {
        default_type application/json;
        return 200 '{"origin":"$http_origin","host":"$http_host","authorization":"$http_authorization","cookie":"$http_cookie","upgrade":"$http_upgrade"}';
    }
}''')
        try:
            command(['docker', 'network', 'create', '--label', 'modelone.validation=true', network])
            network_created = True
            command(['docker', 'run', '--detach', '--pull', 'never', '--name', upstream,
                     '--label', 'modelone.validation=true', '--network', network,
                     '--network-alias', 'myapp', '--network-alias', 'kubeflow-dashboard.infra',
                     '--mount', 'type=bind,source=%s,target=/etc/nginx/conf.d/default.conf,readonly' % echo_config,
                     args.image])
            upstream_created = True
            config_mount = []
            if args.nginx_config:
                config_mount = ['--mount', 'type=bind,source=%s,target=/etc/nginx/conf.d/default.conf,readonly'
                                % args.nginx_config.resolve()]
            command(['docker', 'run', '--detach', '--pull', 'never', '--name', container,
                     '--label', 'modelone.validation=true', '--network', network,
                     '--publish', '127.0.0.1::80', '--mount',
                     'type=bind,source=%s,target=/data/web/frontend/blocked.js.map,readonly' % fixture,
                     *config_mount, args.image])
            created = True
            port = command(['docker', 'inspect', container, '--format', '{{(index (index .NetworkSettings.Ports "80/tcp") 0).HostPort}}'])
            origin = 'http://127.0.0.1:' + port

            def fetch(path):
                with urlopen(origin + path, timeout=5) as response:
                    return response.headers.get('Content-Type', ''), response.read().decode('utf-8')

            deadline = time.monotonic() + 30
            while True:
                try:
                    fetch('/frontend/index.html')
                    break
                except (URLError, HTTPException, ConnectionError, TimeoutError):
                    if time.monotonic() >= deadline:
                        raise RuntimeError('Nginx did not become ready') from None
                    if command(['docker', 'inspect', container, '--format', '{{.State.Running}}']) != 'true':
                        raise RuntimeError('Validation container stopped: ' + command(['docker', 'logs', container])) from None
                    time.sleep(0.5)
            for forwarded_proto in ('http', 'https'):
                connection = HTTPConnection('127.0.0.1', int(port), timeout=5)
                try:
                    connection.request('GET', '/', headers={'Host': 'modelone.example.test',
                                                           'X-Forwarded-Proto': forwarded_proto})
                    response = connection.getresponse()
                    if response.status != 301 or response.getheader('Location') != '/frontend/':
                        raise AssertionError('Root redirect must retain the browser scheme and host')
                    response.read()
                finally:
                    connection.close()
            report['checks'].append('root redirect is relative for both HTTP and HTTPS gateway requests')
            # Browser Origin must survive the proxy, including during upgrade.
            # Suppressing it would bypass the backend's cross-origin login guard.
            for supplied_origin, upgrade in ((None, ''), ('null', ''), ('https://foreign.invalid', ''),
                                             ('http://modelone.example.test', ''), ('https://foreign.invalid', 'websocket')):
                headers = {'Host': 'modelone.example.test', 'Authorization': 'Bearer proxy-fixture',
                           'Cookie': 'session=proxy-fixture'}
                if supplied_origin is not None:
                    headers['Origin'] = supplied_origin
                if upgrade:
                    headers.update(Upgrade=upgrade, Connection='upgrade')
                connection = HTTPConnection('127.0.0.1', int(port), timeout=5)
                try:
                    connection.request('GET', '/_modelone_proxy_probe', headers=headers)
                    response = connection.getresponse()
                    if response.status != 200:
                        raise AssertionError('Proxy probe did not reach the upstream')
                    observed = json.loads(response.read())
                    expected = {'origin': supplied_origin or '', 'host': headers['Host'],
                                'authorization': headers['Authorization'], 'cookie': headers['Cookie'], 'upgrade': upgrade}
                    if observed != expected:
                        raise AssertionError('Proxy must preserve Origin, Host, credentials and upgrade headers: ' + str(observed))
                finally:
                    connection.close()
            report['checks'].append('proxy preserves absent, null, same-origin, foreign and WebSocket Origin headers plus Host, authorization and cookies')
            for base in ('/frontend', '/static/appbuilder/vison', '/static/appbuilder/visonPlus'):
                _, html = fetch(base + '/index.html')
                if '<title>modelOne' not in html or re.search(r'cube[-_ ]?studio|开源版|商业版', html, re.I):
                    raise AssertionError('Unexpected branding: ' + base)
                content_type, manifest = fetch(base + '/manifest.json')
                if 'json' not in content_type or json.loads(manifest)['short_name'] != 'modelOne':
                    raise AssertionError('Manifest must be JSON with modelOne metadata: ' + base)
                for icon in json.loads(manifest)['icons']:
                    icon_url = urlsplit(icon['src'])
                    if icon_url.scheme or icon_url.netloc:
                        # External enterprise CDN icons are validated by the
                        # release resource gate; this local image test cannot
                        # depend on that network.
                        continue
                    icon_path = icon_url.path if icon_url.path.startswith('/') else base + '/' + icon_url.path
                    _, asset = fetch(icon_path)
                    if '<svg' not in asset:
                        raise AssertionError('Missing PWA icon: ' + base)
                _, assets = fetch(base + '/asset-manifest.json')
                for entry in json.loads(assets)['entrypoints']:
                    entry_path = entry if entry.startswith('/') else base + '/' + entry.lstrip('./')
                    content_type, content = fetch(entry_path)
                    if 'text/html' in content_type or not content:
                        raise AssertionError('Missing compiled entrypoint: ' + entry_path)
                report['checks'].append(base + ': branded HTML, PWA, icon and compiled entrypoints')
            for path in ('/frontend/blocked.js.map', '/frontend/blocked.js.map?v=1', '/static/appbuilder/vison/any.js.map'):
                try:
                    fetch(path)
                except HTTPError as error:
                    if error.code != 404:
                        raise
                else:
                    raise AssertionError('Source map must return 404: ' + path)
            report['checks'].append('source map HTTP requests return 404 even when a map exists')
            license_text = subprocess.check_output(['docker', 'exec', container, 'cat', '/usr/share/licenses/modelone/LICENSE'])
            if license_text != (ROOT / 'LICENSE').read_bytes():
                raise AssertionError('Image must include the original LICENSE verbatim')
            report['checks'].append('image contains the unmodified original LICENSE')
            report['status'] = 'passed'
        except Exception as error:
            report['status'] = 'failed'
            report['error'] = str(error)
            raise
        finally:
            if created:
                command(['docker', 'rm', '--force', '--volumes', container])
            if upstream_created:
                command(['docker', 'rm', '--force', '--volumes', upstream])
            if network_created:
                command(['docker', 'network', 'rm', network])
            report['finishedAt'] = datetime.now(timezone.utc).isoformat()
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for name in report['checks']:
        print('PASS: ' + name)
    print('Validation report: ' + str(args.report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, help='locally built frontend image; never pulled automatically')
    parser.add_argument('--nginx-config', type=Path, help='also validate a mounted deployment Nginx configuration')
    parser.add_argument('--report', type=Path, default=ROOT / 'dist/modelone/frontend-image-validation.json')
    run(parser.parse_args())
