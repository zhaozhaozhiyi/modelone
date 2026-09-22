#!/usr/bin/env python3
"""Collect declared dependencies and available license evidence for delivery."""
import hashlib
import json
from pathlib import Path
import shutil
import uuid
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
output = ROOT / 'dist/modelone/compliance'
output.mkdir(parents=True, exist_ok=True)
shutil.copy2(ROOT / 'LICENSE', output / 'LICENSE')
records = []
for app in ('frontend','vision','visionPlus'):
    lock = json.loads((ROOT / 'myapp' / app / 'package-lock.json').read_text())
    for key, pkg in lock.get('packages', {}).items():
        if not key:
            continue
        name = key.split('node_modules/')[-1]
        license_id = pkg.get('license', 'UNKNOWN')
        local = ROOT / 'myapp' / app / key
        candidates = list(local.glob('LICENSE*')) + list(local.glob('license*')) + list(local.glob('COPYING*')) + list(local.glob('NOTICE*'))
        evidence = []
        for file in candidates:
            if file.is_file():
                target = output / app / key / file.name
                target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(file,target)
                evidence.append(str(target.relative_to(output)))
        records.append({'application':app, 'name':name, 'version':pkg.get('version'), 'declaredLicense':license_id, 'evidence':evidence, 'reviewRequired': license_id=='UNKNOWN' or not evidence})
for file in ROOT.glob('*requirements*.txt'):
    shutil.copy2(file,output/file.name)
    records.append({'application':'backend','source':file.name,'reviewRequired':True,'note':'Declared dependencies only; resolve exact installed versions and notices from the final runtime image.'})
(output/'dependencies.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n')
components_by_ref = {}
for record in records:
    if record.get('application') == 'backend' or not record.get('name'):
        continue
    name = record['name']
    version = record.get('version') or 'UNKNOWN'
    encoded_name = quote(name, safe='/-._~')
    purl = 'pkg:npm/%s@%s' % (encoded_name, quote(str(version), safe='._+-'))
    license_id = record.get('declaredLicense', 'UNKNOWN')
    component = {
        'type': 'library',
        'bom-ref': '%s:%s' % (record['application'], purl),
        'name': name,
        'version': version,
        'purl': purl,
        'properties': [{'name': 'modelone:application', 'value': record['application']}],
    }
    if isinstance(license_id, str) and license_id and license_id != 'UNKNOWN':
        key = license_id.replace('.', '').replace('-', '').replace('+', '').replace('_', '')
        license_entry = {'id': license_id} if key.isalnum() else {'name': license_id}
        component['licenses'] = [{'license': license_entry}]
    components_by_ref[component['bom-ref']] = component
components = [components_by_ref[key] for key in sorted(components_by_ref)]
fingerprint = hashlib.sha256('\n'.join(item['bom-ref'] for item in components).encode()).hexdigest()
sbom = {
    'bomFormat': 'CycloneDX',
    'specVersion': '1.5',
    'serialNumber': 'urn:uuid:' + str(uuid.UUID(hex=fingerprint[:32])),
    'version': 1,
    'metadata': {'tools': [{'vendor': 'modelOne', 'name': 'compliance_inventory.py'}]},
    'components': components,
}
(output/'frontend-sbom.cdx.json').write_text(json.dumps(sbom,ensure_ascii=False,indent=2)+'\n')
(output/'README.md').write_text(
    '# Third-party license evidence\n\n'
    'The original LICENSE is copied verbatim. Frontend notices come from installed locked dependencies. '
    '`frontend-sbom.cdx.json` is a CycloneDX 1.5 inventory for the three frontend lock files. '
    'UNKNOWN and reviewRequired entries must be resolved before production delivery. '
    'Backend Python packages, OS packages, base images, GPU libraries and runtime images require a separate '
    'SBOM from the final container images (scripts/image_compliance.py collects evidence for modelOne images); '
    'this report is not a completed legal audit.\n'
)
print('%s dependency entries; %s require review' % (len(records),sum(bool(r['reviewRequired']) for r in records)))
