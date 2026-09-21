#!/usr/bin/env python3
"""Check real frontend HTTP responses from a locally built image on loopback.

Tests static delivery only; no backend, registry, browser or cluster is used.
An intentionally mounted source map proves the web server denies publication.
"""
import argparse
from http.client import HTTPException
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

ROOT = Path(__file__).resolve().parents[1]


def command(args):
    return subprocess.check_output(args, text=True).strip()


def run(args):
    token = secrets.token_hex(6)
    container = 'modelone-web-test-' + token
    report = {'startedAt': datetime.now(timezone.utc).isoformat(), 'image': args.image,
              'imageId': command(['docker', 'image', 'inspect', args.image, '--format', '{{.Id}}']),
              'scope': 'Real Nginx static HTTP responses; not a browser or authenticated backend test.', 'checks': []}
    created = False
    with tempfile.TemporaryDirectory(prefix='modelone-web-test-') as folder:
        fixture = Path(folder) / 'blocked.js.map'
        fixture.write_text('{"sourcesContent":["must not be public"]}')
        try:
            command(['docker', 'run', '--detach', '--pull', 'never', '--name', container,
                     '--label', 'modelone.validation=true', '--add-host', 'myapp:127.0.0.1',
                     '--publish', '127.0.0.1::80', '--mount',
                     'type=bind,source=%s,target=/data/web/frontend/blocked.js.map,readonly' % fixture,
                     args.image])
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
            for base in ('/frontend', '/static/appbuilder/vison', '/static/appbuilder/visonPlus'):
                _, html = fetch(base + '/index.html')
                if '<title>modelOne' not in html or re.search(r'cube[-_ ]?studio|开源版|商业版', html, re.I):
                    raise AssertionError('Unexpected branding: ' + base)
                content_type, manifest = fetch(base + '/manifest.json')
                if 'json' not in content_type or json.loads(manifest)['short_name'] != 'modelOne':
                    raise AssertionError('Manifest must be JSON with modelOne metadata: ' + base)
                for icon in json.loads(manifest)['icons']:
                    _, asset = fetch(base + '/' + icon['src'])
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
            report['finishedAt'] = datetime.now(timezone.utc).isoformat()
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    for name in report['checks']:
        print('PASS: ' + name)
    print('Validation report: ' + str(args.report))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, help='locally built frontend image; never pulled automatically')
    parser.add_argument('--report', type=Path, default=ROOT / 'dist/modelone/frontend-image-validation.json')
    run(parser.parse_args())
