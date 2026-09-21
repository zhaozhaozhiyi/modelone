"""Image packaging contracts; optional real save/load of an already cached image."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundle', ROOT / 'scripts/image_bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.folder = Path(self.directory.name)

    def plan(self, images=None):
        return bundle.generate(images or ['modelone/notebook:v1', 'redis:7'], 'registry.example.test/team', self.folder)

    def test_product_images_are_enterprise_inputs_and_names_do_not_collide(self):
        plan = json.loads(self.plan(['modelone/notebook:v1', 'org/tool:v1', 'org-tool:v1']).read_text())
        product = next(row for row in plan['images'] if row['runtime'].startswith('modelone/'))
        self.assertEqual(product['source'], product['target'])
        self.assertTrue(product['source'].startswith('registry.example.test/team/modelone/'))
        self.assertEqual(len({r['archive'] for r in plan['images']}), 3)
        self.assertEqual(len({r['target'] for r in plan['images']}), 3)
        self.assertEqual((self.folder / 'licenses/LICENSE').read_bytes(), (ROOT / 'LICENSE').read_bytes())

    def test_shell_metacharacters_in_inputs_are_rejected_without_output(self):
        for registry in ('registry.example.test/$(id)', 'https://registry.example.test', 'registry.example.test/team/modelone'):
            with self.assertRaises(ValueError):
                bundle.generate(['redis:7'], registry, self.folder / 'output')
        with self.assertRaises(ValueError):
            self.plan(['redis:7;echo injected'])
        self.assertFalse((self.folder / 'images.json').exists())

    def test_copy_failure_stops_before_pushing_or_processing_later_images(self):
        plan = self.plan()
        with patch.object(bundle.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, ['docker', 'pull'])) as command:
            with self.assertRaises(subprocess.CalledProcessError):
                bundle.execute(plan, 'copy-images')
        self.assertEqual(command.call_count, 1)

    def test_all_archive_checksums_are_checked_before_first_import(self):
        plan_path = self.plan()
        plan = json.loads(plan_path.read_text())
        for row in plan['images']:
            path = self.folder / row['archive']
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b'archive-fixture')
            row.update(sha256=bundle.file_digest(path), imageId='sha256:fixture')
        (self.folder / plan['images'][-1]['archive']).write_bytes(b'corrupt')
        bundle.write_plan(plan_path, plan)
        with patch.object(bundle.subprocess, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'mismatched'):
                bundle.execute(plan_path, 'load')
        command.assert_not_called()

    def test_failed_export_does_not_create_verified_archive(self):
        plan_path = self.plan(['modelone/notebook:v1'])
        class FailedSave:
            stdout = io.BytesIO(b'incomplete archive')
            def wait(self): return 1
            def poll(self): return 1
        with patch.object(bundle, 'inspect', return_value={'imageId': 'sha256:fixture', 'platform': 'linux/amd64'}), patch.object(bundle.subprocess, 'Popen', return_value=FailedSave()):
            with self.assertRaisesRegex(ValueError, 'save failed'):
                bundle.execute(plan_path, 'save')
        row = json.loads(plan_path.read_text())['images'][0]
        self.assertNotIn('sha256', row)
        self.assertFalse((self.folder / row['archive']).exists())

    def test_rendered_manifest_includes_init_containers_and_rejects_templates(self):
        path = self.folder / 'deployment.yaml'
        path.write_text('spec:\n  initContainers:\n  - image: busybox:1.36\n  containers:\n  - image: redis:7\n')
        self.assertEqual(bundle.manifest_images([path]), ['busybox:1.36', 'redis:7'])
        path.write_text('image: "${IMAGE}"\n')
        with self.assertRaises(ValueError):
            bundle.manifest_images([path])

    def test_deployment_rewrite_updates_containers_and_rejects_unplanned_images(self):
        plan = self.plan(['redis:7', 'busybox:1.36'])
        mapping = bundle.image_mapping(plan)
        document = {'spec': {'initContainers': [{'image': 'busybox:1.36'}],
                             'containers': [{'image': 'redis:7'}]},
                    'metadata': {'name': 'compatible-service'}}
        bundle.rewrite_images(document, mapping)
        self.assertEqual(document['metadata']['name'], 'compatible-service')
        self.assertEqual(document['spec']['containers'][0]['image'], mapping['redis:7'])
        self.assertEqual(document['spec']['initContainers'][0]['image'], mapping['busybox:1.36'])
        with self.assertRaisesRegex(ValueError, 'missing from the transfer plan'):
            bundle.rewrite_images({'image': 'unplanned/image:v1'}, mapping)

    @unittest.skipUnless(os.environ.get('MODELONE_BUNDLE_TEST_IMAGE'), 'optional cached-image integration check')
    def test_real_local_save_load_and_corruption_rejection(self):
        runtime = 'modelone/bundle-test:' + uuid.uuid4().hex
        plan = self.plan([runtime])
        target = json.loads(plan.read_text())['images'][0]['target']
        subprocess.run(['docker', 'tag', os.environ['MODELONE_BUNDLE_TEST_IMAGE'], target], check=True)
        try:
            before = bundle.inspect(target)
            bundle.execute(plan, 'save')
            subprocess.run(['docker', 'image', 'rm', target], check=True, capture_output=True)
            bundle.execute(plan, 'load')
            self.assertEqual(bundle.inspect(target), before)
            row = json.loads(plan.read_text())['images'][0]
            with (self.folder / row['archive']).open('ab') as archive:
                archive.write(b'corrupt')
            with self.assertRaisesRegex(ValueError, 'mismatched'):
                bundle.execute(plan, 'load')
        finally:
            subprocess.run(['docker', 'image', 'rm', target], capture_output=True)


if __name__ == '__main__':
    unittest.main()
