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
from urllib.parse import unquote, urlsplit
from urllib.request import urlopen
import shutil
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = 'ccr.ccs.tencentyun.com/cube-studio/'
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
    for source in snapshot['resources']:
        row = dict(source)
        identity = (row['kind'], row['source'])
        if identity in seen:
            continue
        seen.add(identity)
        row['target'] = (brand.image_repository(row['source'][len(REGISTRY):]) if row['kind'] == 'image' else brand.brand_asset(row['path']))
        row['status'] = 'template' if any(field for _, field, _, _ in Formatter().parse(row['source']) if field) else 'pending'
        records.append(row)
    return records

def run(args):
    records = inventory()
    for row in records:
        if row['kind'] == 'image' and args.copy_images:
            if not brand.BRAND['image_registry']:
                raise ValueError('MODELONE_IMAGE_REGISTRY is required for image copying')
            subprocess.run(['skopeo','copy','--all','docker://' + row['source'],'docker://' + row['target']], check=True)
            source_digest = subprocess.check_output(['skopeo','inspect','--format','{{.Digest}}','docker://' + row['source']], text=True).strip()
            target_digest = subprocess.check_output(['skopeo','inspect','--format','{{.Digest}}','docker://' + row['target']], text=True).strip()
            if source_digest != target_digest:
                raise ValueError('Image digest mismatch: ' + row['target'])
            row.update(status='verified', digest=target_digest)
        if row['kind'] == 'asset' and args.download_assets and row['status'] == 'pending':
            destination = (args.download_assets / row['path']).resolve()
            destination.relative_to(args.download_assets.resolve())
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_suffix(destination.suffix + '.part')
            with urlopen(row['source'], timeout=60) as response, temporary.open('wb') as output:
                shutil.copyfileobj(response, output)
            hasher = hashlib.sha256()
            with temporary.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
            temporary.replace(destination)
            row.update(status='downloaded', sha256=digest, size=destination.stat().st_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
    print('%s images, %s assets inventoried (%s templates); report: %s' % (sum(r['kind']=='image' for r in records), sum(r['kind']=='asset' for r in records), sum(r['status']=='template' for r in records), args.output))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT / 'dist/modelone/resource-inventory.json')
    parser.add_argument('--copy-images',action='store_true')
    parser.add_argument('--download-assets',type=Path)
    run(parser.parse_args())
