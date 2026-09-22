#!/usr/bin/env python3
"""Collect SBOMs and license evidence from an immutable, locally cached image.

Requires Docker and Syft. Never pulls, pushes, starts the image or enriches
package metadata over the network. Results still require license review.
"""
import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config/modelone-syft.yaml'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    path.chmod(0o600)


def materialize(scan, output, image_id, original_license):
    """Keep package evidence, omitting the raw container environment/history."""
    source = scan.get('source', {})
    metadata = source.get('metadata', {})
    if source.get('type') != 'image' or metadata.get('imageID') != image_id:
        raise ValueError('SBOM source does not match the inspected local image ID')
    packages = scan.get('artifacts', [])
    if not packages:
        raise ValueError('Image scan found no packages; delivery evidence is incomplete')
    source['metadata'] = {key: metadata[key] for key in (
        'imageID', 'manifestDigest', 'mediaType', 'tags', 'imageSize', 'repoDigests', 'architecture', 'os'
    ) if key in metadata}
    descriptor = scan.get('descriptor', {})
    scan['descriptor'] = {key: descriptor[key] for key in ('name', 'version') if key in descriptor}
    evidence = []
    file_evidence = {}
    path_evidence = {}
    original_found = False
    for file in scan.get('files', []):
        if 'contents' not in file:
            continue
        path = file.get('location', {}).get('path', '')
        data = base64.b64decode(file['contents'], validate=True)
        # Content-addressed names cannot escape the output directory, even for
        # unusual paths inside a scanned image. Original locations stay in JSON.
        relative = 'licenses/' + digest(data) + '.txt'
        target = output / relative
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        target.chmod(0o600)
        entry = {'sourcePath': path, 'fileId': file['id'], 'file': relative,
                 'sha256': digest(data), 'bytes': len(data)}
        evidence.append(entry)
        file_evidence[file['id']] = relative
        path_evidence[path] = relative
        if path == '/usr/share/licenses/modelone/LICENSE':
            if data != original_license:
                raise ValueError('Image product LICENSE differs from the unmodified source LICENSE')
            original_found = True
    if not original_found:
        raise ValueError('Image scan did not capture /usr/share/licenses/modelone/LICENSE')
    owned = {}
    for relationship in scan.get('artifactRelationships', []):
        if relationship.get('type') in ('contains', 'evident-by') and relationship.get('child') in file_evidence:
            owned.setdefault(relationship['parent'], set()).add(file_evidence[relationship['child']])
    review = []
    for package in packages:
        files = set(owned.get(package['id'], ()))
        locations = package.get('locations', []) + [location for item in package.get('licenses', [])
                                                    for location in item.get('locations', [])]
        for location in locations:
            if location.get('path') in path_evidence:
                files.add(path_evidence[location['path']])
            path = PurePosixPath(location.get('path', ''))
            for evidence_path, relative in path_evidence.items():
                evidence_location = PurePosixPath(evidence_path)
                if package['type'] == 'python' and path.parent.name.endswith(('.dist-info', '.egg-info')):
                    if evidence_location.is_relative_to(path.parent):
                        files.add(relative)
                elif package['type'] == 'npm' and path.name == 'package.json':
                    # Adjacent notices belong to this package; nested node_modules
                    # and vendor packages require their own records/review.
                    if evidence_location.parent == path.parent:
                        files.add(relative)
        licenses = sorted({item.get('spdxExpression') or item.get('value', '')
                           for item in package.get('licenses', [])} - {''})
        review.append({'id': package['id'], 'name': package['name'], 'version': package.get('version'),
                       'type': package['type'], 'purl': package.get('purl'), 'declaredLicenses': licenses,
                       'evidence': sorted(files), 'reviewRequired': True,
                       'issues': (['missing-license-declaration'] if not licenses else [])
                                 + (['missing-associated-license-file'] if not files else [])})
    write_json(output / 'syft.json', scan)
    write_json(output / 'license-evidence.json', evidence)
    write_json(output / 'review.json', review)
    (output / 'LICENSE').write_bytes(original_license)
    (output / 'LICENSE').chmod(0o600)
    return {'packageCount': len(packages), 'packageTypes': dict(sorted(Counter(p['type'] for p in packages).items())),
            'licenseFileCount': len(evidence), 'uniqueLicenseFiles': len(set(file_evidence.values())),
            'packagesMissingLicense': sum(not row['declaredLicenses'] for row in review),
            'packagesMissingAssociatedEvidence': sum(not row['evidence'] for row in review),
            'reviewRequired': True, 'originalLicenseVerified': True}


def collect(image, output, syft='syft'):
    if image.startswith('-') or not image.strip() or any(c.isspace() for c in image):
        raise ValueError('Provide a local image reference or sha256 ID')
    if output.exists():
        raise ValueError('Output already exists; use a new directory to preserve prior evidence')
    for tool in ('docker', syft):
        if not shutil.which(tool):
            raise ValueError(tool + ' is required')
    env = {key: value for key, value in os.environ.items() if not key.startswith('SYFT_')}
    env['SYFT_CHECK_FOR_APP_UPDATE'] = 'false'

    def run(argv):
        return subprocess.run(argv, check=True, capture_output=True, text=True, env=env).stdout

    # Inspect only the required field, never dump image environment variables.
    image_id = run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}']).strip()
    if not re.fullmatch(r'sha256:[0-9a-f]{64}', image_id):
        raise ValueError('Local image ID is invalid')
    started = datetime.now(timezone.utc).isoformat()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.modelone-compliance-', dir=output.parent) as folder:
        stage = Path(folder)
        raw = stage / 'raw.syft.json'
        print('Scanning local image ' + image_id + '; package enrichment disabled', flush=True)
        run([syft, 'scan', 'docker:' + image_id, '--config', str(CONFIG), '-o', 'syft-json=' + str(raw)])
        result = stage / 'result'
        result.mkdir(mode=0o700)
        summary = materialize(json.loads(raw.read_text()), result, image_id, (ROOT / 'LICENSE').read_bytes())
        # Convert the filtered report so raw image config/history never reaches
        # the delivered CycloneDX/SPDX files either.
        run([syft, 'convert', str(result / 'syft.json'), '--config', str(CONFIG),
             '-o', 'cyclonedx-json@1.5=' + str(result / 'sbom.cdx.json'),
             '-o', 'spdx-json@2.3=' + str(result / 'sbom.spdx.json')])
        cdx = json.loads((result / 'sbom.cdx.json').read_text())
        spdx = json.loads((result / 'sbom.spdx.json').read_text())
        if (cdx.get('bomFormat') != 'CycloneDX' or cdx.get('specVersion') != '1.5'
                or not cdx.get('components') or spdx.get('spdxVersion') != 'SPDX-2.3' or not spdx.get('packages')):
            raise ValueError('Missing or unsupported converted SBOM output')
        (result / 'README.md').write_text(
            '# modelOne runtime image license evidence\n\n'
            'This inventory is bound to the immutable local image ID in summary.json. '
            'Syft scans the final filesystem without executing the image or enabling remote enrichment. '
            'syft.json retains package evidence; sbom.cdx.json and sbom.spdx.json provide standard SBOMs. '
            'license-evidence.json maps original image paths to byte-preserved license files and SHA-256 values. '
            'The product LICENSE is verified against the source.\n\n'
            'All packages still require legal review. Missing declarations/files are listed in review.json. '
            'Files larger than the configured collection limit, unrecognized binaries and separately mounted '
            'assets may need additional evidence. This is not a vulnerability scan or complete legal audit. '
            'Raw image environment/history is omitted; package metadata and original notices remain internal '
            'delivery evidence and should be reviewed before sharing.\n')
        summary.update(image=image, imageId=image_id, startedAt=started,
                       finishedAt=datetime.now(timezone.utc).isoformat(),
                       tool=json.loads((result / 'syft.json').read_text())['descriptor'],
                       configSha256=digest(CONFIG.read_bytes()), status='collected')
        write_json(result / 'summary.json', summary)
        checksums = {str(path.relative_to(result)): digest(path.read_bytes())
                     for path in sorted(result.rglob('*')) if path.is_file()}
        write_json(result / 'checksums.json', checksums)
        for path in result.rglob('*'):
            path.chmod(0o700 if path.is_dir() else 0o600)
        if output.exists():
            raise ValueError('Output appeared during scan; refusing to overwrite')
        result.rename(output)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--image', required=True, help='locally cached image; no pull fallback')
    parser.add_argument('--output', required=True, type=Path, help='new evidence directory')
    parser.add_argument('--syft-command', default='syft', help='Syft executable path, including CI tool-cache paths')
    args = parser.parse_args()
    try:
        collect(args.image, args.output.resolve(), args.syft_command)
    except subprocess.CalledProcessError as error:
        parser.exit(1, 'Image evidence collection failed in ' + Path(error.cmd[0]).name
                    + ' (exit ' + str(error.returncode) + '); no delivery output was published.\n')
    except (ValueError, OSError) as error:
        parser.error(str(error))
