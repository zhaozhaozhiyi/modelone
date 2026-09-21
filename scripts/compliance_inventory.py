#!/usr/bin/env python3
"""Collect declared dependencies and available license evidence for delivery."""
import json
from pathlib import Path
import shutil

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
(output/'README.md').write_text('# Third-party license evidence\n\nThe original LICENSE is copied verbatim. Frontend notices come from installed locked dependencies. UNKNOWN and reviewRequired entries must be resolved before production delivery. Backend and OS/image components require an SBOM from the final container images; this report is not a completed legal audit.\n')
print('%s dependency entries; %s require review' % (len(records),sum(bool(r['reviewRequired']) for r in records)))
