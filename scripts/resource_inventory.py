#!/usr/bin/env python3
"""Inventory original owned resources; optional explicit copy to enterprise storage.

Uses the committed source snapshot to retain original URLs after replacements. No network by default.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import urlopen
import shutil
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = 'ccr.ccs.tencentyun.com/cube-studio/'
ARGO_REGISTRY = 'ccr.ccs.tencentyun.com/cube-argoproj/'
BUCKET = 'cube-studio.oss-cn-hangzhou.aliyuncs.com'
spec = importlib.util.spec_from_file_location('brand', ROOT / 'myapp/brand.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

def inventory():
    # Persist the original source snapshot so subsequent brand commits do not
    # erase migration provenance. Targets are resolved from current config.
    snapshot = json.loads((ROOT / 'config/resource-sources.json').read_text())
    records = []
    seen = set()
    sources = []
    for source in snapshot['resources']:
        if source['source'] == 'https://' + BUCKET + '/aihub/aigc/aigc{i+1}.jpeg':
            # Chat.aigc4 emits exactly four examples (pic_num=4), not an
            # arbitrary Python expression to evaluate from inventory data.
            for number in range(1, 5):
                sources.append({**source, 'sourceTemplate': source['source'],
                                'source': source['source'].replace('{i+1}', str(number)),
                                'path': source['path'].replace('{i+1}', str(number))})
        else:
            sources.append(source)
    for source in sources:
        row = dict(source)
        if row['kind'] == 'asset':
            # The original text scan captured the transcript column of ASR CSV
            # rows as part of these URLs. Keep that evidence, download the URL.
            clean = re.sub(r'(/labelstudio/asr/[^/,]+\.wav),.*$', r'\1', row['source'])
            if clean != row['source']:
                row['sourceReference'] = row['source']
                row['source'] = clean
                row['path'] = unquote(urlsplit(clean).path).lstrip('/')
            row['path'] = brand.asset_path(row['path'])
        identity = (row['kind'], row['source'])
        if identity in seen:
            continue
        seen.add(identity)
        if row['kind'] == 'image':
            if row['source'].startswith(REGISTRY):
                row['target'] = brand.image_repository(row['source'][len(REGISTRY):])
            elif row['source'].startswith(ARGO_REGISTRY):
                # Match image_bundle.py's collision-safe third-party target.
                row['target'] = brand.image_repository(
                    'third-party/ccr.ccs.tencentyun.com/argoproj/' + row['source'][len(ARGO_REGISTRY):])
            else:
                raise ValueError('Unsupported image source registry: ' + row['source'])
        else:
            row['target'] = brand.brand_asset(row['path'])
        row['status'] = 'template' if any(field for _, field, _, _ in Formatter().parse(row['source']) if field) else 'pending'
        records.append(row)
    return records

def digest_file(path):
    with path.open('rb') as source:
        return digest_stream(source)[0]


def digest_stream(source):
    hasher, size = hashlib.sha256(), 0
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        hasher.update(chunk)
        size += len(chunk)
    return hasher.hexdigest(), size


def open_url(value, enterprise=False):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname:
        raise ValueError('Resource URL must be absolute HTTP(S)')
    if enterprise and brand.is_legacy_resource_url(value):
        raise ValueError('Enterprise resource uses the original storage host')
    response = urlopen(urlunsplit(parsed._replace(path=quote(parsed.path, safe='/%:@-._~'))), timeout=60)
    if enterprise and brand.is_legacy_resource_url(response.geturl()):
        response.close()
        raise ValueError('Enterprise resource redirects to the original storage host')
    return response


def image_digest(value):
    return subprocess.check_output(
        ['skopeo', 'inspect', '--format', '{{.Digest}}', 'docker://' + value], text=True).strip()


def save_report(path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.part')
    temporary.write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def restore_progress(records, report):
    previous = {(row['kind'], row['source'], row['target']): row for row in report}
    for row in records:
        saved = previous.get((row['kind'], row['source'], row['target']), {})
        if saved.get('path') != row.get('path'):
            continue
        for key in ('sha256', 'size', 'digest'):
            if key in saved:
                row[key] = saved[key]
        # Every release check must re-read the current target. Persisted success
        # alone must not certify deleted or changed remote objects.
        if row.get('sha256'):
            row['status'] = 'downloaded'
        elif row.get('digest'):
            row['status'] = 'copied'


def process_record(row, args):
    if row['status'] == 'template':
        return
    if row['kind'] == 'image':
        if args.copy_images:
            if not brand.BRAND['image_registry']:
                raise ValueError('MODELONE_IMAGE_REGISTRY is required for image copying')
            subprocess.run(['skopeo', 'copy', '--all', '--preserve-digests',
                            'docker://' + row['source'], 'docker://' + row['target']], check=True)
        if args.copy_images or args.verify_targets:
            source_digest = row.get('digest') or image_digest(row['source'])
            target_digest = image_digest(row['target'])
            if source_digest != target_digest:
                raise ValueError('Image digest mismatch')
            row.update(status='verified', digest=target_digest)
        return
    if args.download_assets:
        destination = (args.download_assets / row['path']).resolve()
        destination.relative_to(args.download_assets.resolve())
        if not (destination.is_file() and row.get('sha256') == digest_file(destination)):
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + '.part')
            with open_url(row['source']) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            temporary.replace(destination)
        row.update(status='downloaded', sha256=digest_file(destination), size=destination.stat().st_size)
    if args.verify_targets:
        if not row.get('sha256'):
            with open_url(row['source']) as source:
                row['sha256'], row['size'] = digest_stream(source)
        with open_url(row['target'], enterprise=True) as target:
            digest, size = digest_stream(target)
        if digest != row['sha256'] or size != row['size']:
            raise ValueError('Asset checksum mismatch')
        row['status'] = 'verified'


def run(args):
    records = inventory()
    if args.require_complete or args.verify_targets:
        brand.validate_release_settings(include_links=False)
    if args.resume:
        restore_progress(records, json.loads(args.resume.read_text()))
    failures = 0
    for row in records:
        try:
            process_record(row, args)
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            row.update(status='failed', error=type(error).__name__)
            failures += 1
        # Save each operation so interrupted migrations can be resumed.
        if args.copy_images or args.download_assets or args.verify_targets:
            save_report(args.output, records)
    save_report(args.output, records)
    if args.require_complete:
        incomplete = [row for row in records if row['status'] != 'verified']
        if incomplete:
            raise ValueError('%s resources are not verified at enterprise targets; '
                             'upload assets, then run --verify-targets --resume <report>' % len(incomplete))
    if failures:
        raise ValueError('%s resource operations failed; inspect the saved report' % failures)
    print('%s images, %s assets inventoried (%s templates); report: %s' % (sum(r['kind']=='image' for r in records), sum(r['kind']=='asset' for r in records), sum(r['status']=='template' for r in records), args.output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/modelone/resource-inventory.json')
    parser.add_argument('--copy-images', action='store_true')
    parser.add_argument('--download-assets', type=Path)
    parser.add_argument('--resume', type=Path, help='reuse checksums from an earlier report with identical source and target')
    parser.add_argument('--verify-targets', action='store_true', help='read enterprise assets and image digests and compare with source checksums')
    parser.add_argument('--require-complete', action='store_true', help='fail unless every target was verified during this run')
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, OSError) as error:
        parser.error(str(error))
