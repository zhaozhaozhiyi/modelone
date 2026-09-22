"""Verify image provenance, byte-preserved notices and fail-closed evidence output."""
import base64
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import image_compliance as compliance

IMAGE_ID = 'sha256:' + 'a' * 64
LICENSE = (compliance.ROOT / 'LICENSE').read_bytes()


def sample():
    return {
        'source': {'type': 'image', 'metadata': {'imageID': IMAGE_ID, 'config': 'private-env',
                                               'manifest': 'image-history', 'architecture': 'amd64'}},
        'descriptor': {'name': 'syft', 'version': '1.51.1', 'configuration': {'registry': 'private-auth'}},
        'artifacts': [
            {'id': 'pkg1', 'name': 'installed', 'type': 'python', 'version': '1.0',
             'licenses': [{'value': 'MIT'}]},
            {'id': 'pkg2', 'name': 'unresolved', 'type': 'binary', 'version': '2.0', 'licenses': []},
        ],
        'files': [
            {'id': 'license', 'location': {'path': '/usr/share/licenses/modelone/LICENSE'},
             'contents': base64.b64encode(LICENSE).decode()},
            {'id': 'notice', 'location': {'path': '/../../NOTICE'},
             'contents': base64.b64encode(b'Copyright example\r\nUnmodified bytes\xff').decode()},
        ],
        'artifactRelationships': [{'parent': 'pkg1', 'child': 'notice', 'type': 'contains'}],
    }


class ComplianceTests(unittest.TestCase):
    def test_exact_notice_bytes_paths_missing_evidence_and_private_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            result = compliance.materialize(sample(), output, IMAGE_ID, LICENSE)
            self.assertEqual(result['packageCount'], 2)
            self.assertEqual(result['packagesMissingLicense'], 1)
            self.assertEqual(result['packagesMissingAssociatedEvidence'], 1)
            self.assertTrue(result['originalLicenseVerified'])
            self.assertEqual((output / 'LICENSE').read_bytes(), LICENSE)
            evidence = json.loads((output / 'license-evidence.json').read_text())
            notice = next(row for row in evidence if row['sourcePath'] == '/../../NOTICE')
            self.assertEqual((output / notice['file']).read_bytes(), b'Copyright example\r\nUnmodified bytes\xff')
            self.assertTrue((output / notice['file']).resolve().is_relative_to(output.resolve()))
            self.assertEqual((output / notice['file']).stat().st_mode & 0o077, 0)
            records = json.loads((output / 'review.json').read_text())
            self.assertEqual(records[0]['evidence'], [notice['file']])
            self.assertTrue(all(row['reviewRequired'] for row in records))
            text = (output / 'syft.json').read_text()
            for secret in ('private-env', 'image-history', 'private-auth'):
                self.assertNotIn(secret, text)

    def test_foreign_image_empty_scan_missing_or_modified_original_license_rejected(self):
        bad = []
        value = sample()
        value['source']['metadata']['imageID'] = 'sha256:' + 'b' * 64
        bad.append(value)
        value = sample()
        value['artifacts'] = []
        bad.append(value)
        value = sample()
        value['files'] = []
        bad.append(value)
        value = sample()
        value['files'][0]['contents'] = base64.b64encode(b'changed copyright').decode()
        bad.append(value)
        for value in bad:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as folder:
                with self.assertRaises(ValueError):
                    compliance.materialize(copy.deepcopy(value), Path(folder), IMAGE_ID, LICENSE)

    def test_existing_evidence_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            (output / 'summary.json').write_text('prior evidence')
            with patch('image_compliance.subprocess.run') as run:
                with self.assertRaises(ValueError):
                    compliance.collect('modelone/backend:v1', output)
                run.assert_not_called()
            self.assertEqual((output / 'summary.json').read_text(), 'prior evidence')

    def test_metadata_license_paths_do_not_claim_nested_dependency_notices(self):
        scan = sample()
        scan['artifacts'][0]['locations'] = [{'path': '/python/demo.dist-info/METADATA'}]
        scan['artifacts'][1].update(type='npm', locations=[{'path': '/node_modules/demo/package.json'}])
        scan['artifactRelationships'] = []
        for number, path in enumerate(('/python/demo.dist-info/licenses/LICENSE', '/node_modules/demo/LICENSE',
                                     '/node_modules/demo/node_modules/other/LICENSE')):
            scan['files'].append({'id': 'fixture-' + str(number), 'location': {'path': path},
                                  'contents': base64.b64encode(('notice-' + str(number)).encode()).decode()})
        with tempfile.TemporaryDirectory() as folder:
            compliance.materialize(scan, Path(folder), IMAGE_ID, LICENSE)
            records = json.loads((Path(folder) / 'review.json').read_text())
            self.assertEqual(records[0]['evidence'], ['licenses/' + compliance.digest(b'notice-0') + '.txt'])
            self.assertEqual(records[1]['evidence'], ['licenses/' + compliance.digest(b'notice-1') + '.txt'])


if __name__ == '__main__':
    unittest.main()
