"""Regression checks for persisted data and shared configuration (no app startup)."""
import importlib.util
import json
from pathlib import Path
import unittest
import sqlalchemy as sa

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'myapp' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
brand = load('brand')
migration = load('brand_migration')

class BrandTests(unittest.TestCase):
    def test_resource_resolution_is_idempotent(self):
        before = dict(brand.BRAND)
        try:
            brand.BRAND.update(image_registry='registry.example.test/team', asset_base_url='https://assets.example.test')
            data = {'image': 'ccr.ccs.tencentyun.com/cube-studio/notebook:v1', 'command': 'use /cube-studio/aihub', 'url': '/static/assets/modelone/example.zip'}
            result = brand.resolve_resources(data)
            self.assertEqual(result['image'], 'registry.example.test/team/modelone/notebook:v1')
            self.assertEqual(result['command'], data['command'])
            self.assertEqual(result['url'], 'https://assets.example.test/example.zip')
            self.assertEqual(brand.resolve_resources(result), result)
        finally:
            brand.BRAND.clear(); brand.BRAND.update(before)

    def test_sql_migration_preserves_ids_and_handles_optional_modules(self):
        engine = sa.create_engine('sqlite://')
        with engine.begin() as db:
            db.execute(sa.text('CREATE TABLE chat (id INTEGER PRIMARY KEY, name TEXT UNIQUE, label TEXT, hello TEXT, prompt TEXT, knowledge TEXT)'))
            db.execute(sa.text('INSERT INTO chat VALUES (1, :name, :label, NULL, :prompt, :knowledge)'), {'name':'cube-studio', 'label':'CubeStudio', 'prompt':'{{history}}\nHuman:{{query}}\nAI:', 'knowledge':json.dumps({'file':'/mnt/admin/pipeline/example/gpt/cube-studio.csv'})})
            self.assertEqual(migration.migrate_connection(db, brand.BRAND, brand.resolve_resources), 1)
            row = db.execute(sa.text('SELECT * FROM chat')).mappings().one()
            self.assertEqual(row['name'], 'cube-studio')
            self.assertEqual(row['label'], 'modelOne')
            self.assertIsNone(row['hello'])
            self.assertEqual(row['prompt'], '{{history}}\nHuman:{{query}}\nAI:')
            self.assertTrue(json.loads(row['knowledge'])['file'].endswith('/modelone.csv'))
            self.assertEqual(migration.migrate_connection(db, brand.BRAND, brand.resolve_resources), 0)

    def test_chat_protocols(self):
        data = {row['name']:row for row in json.loads((ROOT / 'myapp/init/init-chat.json').read_text())}
        self.assertEqual(data['aigc']['service_config']['data']['prompt'], '$text')
        self.assertEqual(data['tts']['prompt'], '{{query}}')
        self.assertIn('{{history}}', data['native']['prompt'])
        self.assertIn('{{knowledge}}', data['modelone']['prompt'])
        self.assertTrue((ROOT / 'myapp/example/pipeline/gpt/modelone.csv').exists())

    def test_migration_keeps_json_valid_and_removes_old_links(self):
        value = json.dumps({'doc':'https://github.com/data-infra/cube-studio/wiki/usage', 'label':'Cube Studio', 'command':'cd /cube-studio/aihub'})
        result = json.loads(migration.rewrite(value, brand.resolve_resources, '/help'))
        self.assertEqual(result['doc'], '/help')
        self.assertEqual(result['label'], 'modelOne')
        self.assertEqual(result['command'], 'cd /cube-studio/aihub')

    def test_scan_blocks_legacy_text_and_maps(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('scan', ROOT / 'scripts/brand_scan.py')
        scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
        with tempfile.TemporaryDirectory() as folder:
            scan.ROOT = Path(folder); scan.SURFACES = ('surface',); scan.BUILDS = ()
            (scan.ROOT / 'surface').mkdir()
            (scan.ROOT / 'surface/view.py').write_text('label = "CubeStudio"')
            self.assertTrue(scan.scan())
            (scan.ROOT / 'surface/view.py').write_text('label = "modelOne"')
            self.assertFalse(scan.scan())
            (scan.ROOT / 'surface/view.py').write_text('img = "/static/appbuilder/vison/logo.png"')
            self.assertTrue(scan.scan())
            (scan.ROOT / 'surface/view.py').write_text('label = "modelOne"')
            (scan.ROOT / 'surface/app.js.map').write_text('{}')
            self.assertTrue(scan.scan())

if __name__ == '__main__':
    unittest.main()
