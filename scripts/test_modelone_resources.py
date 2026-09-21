"""Verify migration gates against a local HTTP fixture, with no external requests."""
import contextlib
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('resources', ROOT / 'scripts/resource_inventory.py')
resources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(resources)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(self.folder)))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
        (self.folder / 'source.bin').write_bytes(b'expected resource content\x00\xff')
        (self.folder / 'target.bin').write_bytes((self.folder / 'source.bin').read_bytes())
        self.record = {'kind': 'asset', 'source': self.base + '/source.bin',
                       'target': self.base + '/target.bin', 'path': 'nested/file.bin', 'status': 'pending'}
        self.brand = patch.dict(resources.brand.BRAND, image_registry='registry.example.test/team', asset_base_url=self.base)
        self.brand.start()
        self.addCleanup(self.brand.stop)
        self.args = SimpleNamespace(output=self.folder / 'report.json', resume=None, download_assets=None,
                                    copy_images=False, verify_targets=False, require_complete=True)

    def run_inventory(self):
        with patch.object(resources, 'inventory', return_value=[dict(self.record)]):
            resources.run(self.args)

    def report(self):
        return json.loads(self.args.output.read_text())

    def test_download_alone_does_not_pass_release_gate(self):
        self.args.download_assets = self.folder / 'download'
        with self.assertRaisesRegex(ValueError, 'not verified'):
            self.run_inventory()
        self.assertEqual(self.report()[0]['status'], 'downloaded')
        self.assertEqual((self.args.download_assets / self.record['path']).read_bytes(),
                         (self.folder / 'source.bin').read_bytes())

    def test_target_checksum_verification_and_resume_detect_changed_target(self):
        self.args.verify_targets = True
        self.run_inventory()
        self.assertEqual(self.report()[0]['status'], 'verified')
        self.args.resume = self.args.output
        (self.folder / 'source.bin').unlink()  # saved checksum supports offline-source validation
        self.run_inventory()
        (self.folder / 'target.bin').write_bytes(b'incorrect')
        with self.assertRaisesRegex(ValueError, 'not verified'):
            self.run_inventory()
        self.assertEqual(self.report()[0]['status'], 'failed')

    def test_saved_verified_status_cannot_pass_without_rechecking(self):
        self.args.verify_targets = True
        self.run_inventory()
        self.args.resume = self.args.output
        self.args.verify_targets = False
        with self.assertRaisesRegex(ValueError, 'not verified'):
            self.run_inventory()

    def test_missing_target_is_recorded_and_fails_gate(self):
        self.args.verify_targets = True
        (self.folder / 'target.bin').unlink()
        with self.assertRaisesRegex(ValueError, 'not verified'):
            self.run_inventory()
        self.assertEqual(self.report()[0]['error'], 'HTTPError')

    def test_changed_target_does_not_reuse_another_deployments_checksums(self):
        previous = [{**self.record, 'sha256': 'old', 'size': 3, 'status': 'verified'}]
        current = [{**self.record, 'target': self.base + '/other.bin'}]
        resources.restore_progress(current, previous)
        self.assertNotIn('sha256', current[0])
        self.assertEqual(current[0]['status'], 'pending')

    def test_image_digest_mismatch_fails_and_preserves_report(self):
        record = {'kind': 'image', 'source': 'source/image:v1', 'target': 'target/image:v1', 'status': 'pending'}
        self.args.verify_targets = True
        with patch.object(resources, 'inventory', return_value=[record]), patch.object(resources, 'image_digest', side_effect=['sha256:one', 'sha256:two']):
            with self.assertRaisesRegex(ValueError, 'not verified'):
                resources.run(self.args)
        self.assertEqual(self.report()[0]['status'], 'failed')

    def test_release_rejects_relative_assets_and_malformed_registries(self):
        for asset in ('/static/assets/modelone', self.base + '/?token=secret',
                      'https://user:password@example.test/assets'):
            with patch.dict(resources.brand.BRAND, asset_base_url=asset), self.assertRaises(ValueError):
                resources.brand.validate_release_settings(include_links=False)
        for registry in ('https://registry.example.test', 'example.test/$(id)', 'example.test/team/modelone'):
            with patch.dict(resources.brand.BRAND, image_registry=registry), self.assertRaises(ValueError):
                resources.brand.validate_release_settings(include_links=False)

    def test_argo_images_use_the_same_collision_safe_target_as_image_bundle(self):
        rows = resources.inventory()
        argo = next(row for row in rows if row['source'].endswith('/cube-argoproj/argoexec:v3.4.3'))
        self.assertEqual(argo['target'],
                         'registry.example.test/team/modelone/third-party/ccr.ccs.tencentyun.com/argoproj/argoexec:v3.4.3')


if __name__ == '__main__':
    unittest.main()
