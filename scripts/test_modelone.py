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
    def test_migrations_have_one_head_without_starting_application(self):
        from alembic.script import ScriptDirectory
        scripts = ScriptDirectory(str(ROOT / 'myapp/migrations'))
        self.assertEqual(scripts.get_heads(), ['modelone_brand_links_20260921'])
        revisions = list(scripts.iterate_revisions('head', '40e1215ccbd6'))
        self.assertEqual([r.revision for r in revisions], ['modelone_brand_links_20260921', 'modelone_brand_20260921'])

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
            brand.BRAND['asset_base_url'] = 'https://assets.example.test/static/assets/modelone'
            result = brand.resolve_resources(data)
            self.assertEqual(result['url'], 'https://assets.example.test/static/assets/modelone/example.zip')
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

    def test_initial_template_links_use_configured_help(self):
        before = brand.BRAND['help_url']
        try:
            data = {'gitpath': '/job-template/job/tf', 'expand': {'help_url': '/images/ubuntu-gpu'}, 'third_party': 'https://github.com/alibaba/DataX'}
            brand.BRAND['help_url'] = ''
            self.assertEqual(brand.resolve_resources(data)['gitpath'], '')
            brand.BRAND['help_url'] = 'https://help.example.test'
            result = brand.resolve_resources(data)
            self.assertEqual(result['gitpath'], 'https://help.example.test')
            self.assertEqual(result['expand']['help_url'], 'https://help.example.test')
            self.assertEqual(result['third_party'], data['third_party'])
        finally:
            brand.BRAND['help_url'] = before

    def test_migration_keeps_json_valid_and_removes_old_links(self):
        value = json.dumps({'doc':'https://github.com/data-infra/cube-studio/wiki/usage', 'label':'Cube Studio', 'command':'cd /cube-studio/aihub'})
        result = json.loads(migration.rewrite(value, brand.resolve_resources, '/help'))
        self.assertEqual(result['doc'], '/help')
        self.assertEqual(result['label'], 'modelOne')
        self.assertEqual(result['command'], 'cd /cube-studio/aihub')

    def test_migration_covers_persisted_links_and_preview_assets(self):
        engine = sa.create_engine('sqlite://')
        with engine.begin() as db:
            db.execute(sa.text('CREATE TABLE images (id INTEGER PRIMARY KEY, name TEXT, gitpath TEXT)'))
            db.execute(sa.text('CREATE TABLE pipeline (id INTEGER PRIMARY KEY, name TEXT, parameter TEXT)'))
            db.execute(sa.text('CREATE TABLE dataset (id INTEGER PRIMARY KEY, name TEXT, icon TEXT, source TEXT)'))
            db.execute(sa.text('INSERT INTO images VALUES (1, :image, :gitpath)'), {'image': 'ccr.ccs.tencentyun.com/cube-studio/notebook:v1', 'gitpath': 'https://github.com/data-infra/cube-studio/tree/main/images'})
            db.execute(sa.text('INSERT INTO pipeline VALUES (1, :name, :parameter)'), {'name': 'cube-studio-job', 'parameter': json.dumps({'img': 'https://cube-studio.oss-cn-hangzhou.aliyuncs.com/demo.png'})})
            db.execute(sa.text('INSERT INTO dataset VALUES (1, :name, :icon, :source)'), {'name': 'cube-studio-data', 'icon': 'https://cube-studio.oss-cn-hangzhou.aliyuncs.com/dataset.png', 'source': 'cube_studio'})
            self.assertEqual(migration.migrate_connection(db, {'help_url': '/help'}, brand.resolve_resources), 3)
            self.assertEqual(db.execute(sa.text('SELECT gitpath FROM images')).scalar(), '/help')
            row = db.execute(sa.text('SELECT * FROM pipeline')).mappings().one()
            self.assertEqual(row['name'], 'cube-studio-job')
            self.assertEqual(json.loads(row['parameter'])['img'], brand.brand_asset('demo.png'))
            row = db.execute(sa.text('SELECT * FROM dataset')).mappings().one()
            self.assertEqual(row['name'], 'cube-studio-data')
            self.assertEqual(row['source'], 'modelOne')
            self.assertEqual(row['icon'], brand.brand_asset('dataset.png'))
            self.assertEqual(migration.migrate_connection(db, {'help_url': '/help'}, brand.resolve_resources), 0)

    def test_inventory_matches_product_asset_paths(self):
        spec = importlib.util.spec_from_file_location('inventory', ROOT / 'scripts/resource_inventory.py')
        inventory = importlib.util.module_from_spec(spec); spec.loader.exec_module(inventory)
        rows = inventory.inventory()
        source = 'https://cube-studio.oss-cn-hangzhou.aliyuncs.com/cube-studio.mp4'
        video = next(row for row in rows if row['source'] == source)
        self.assertEqual(video['path'], 'tutorial-pipeline.mp4')
        self.assertEqual(video['target'], brand.resolve_resources(source))
        self.assertEqual(brand.resolve_resources(source + '?download=1'), brand.brand_asset('tutorial-pipeline.mp4') + '?download=1')
        self.assertEqual(len({(r['kind'], r['source']) for r in rows}), len(rows))
        audio = [row for row in rows if '/labelstudio/asr/' in row['source']]
        self.assertTrue(audio)
        self.assertTrue(all(row['source'].endswith('.wav') for row in audio))
        examples = [row for row in rows if 'sourceTemplate' in row]
        self.assertEqual(len(examples), 4)
        self.assertTrue(all('{' not in row['source'] for row in examples))

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
            (scan.ROOT / 'surface/view.py').write_text('label = "cube_studio"')
            self.assertTrue(scan.scan())
            (scan.ROOT / 'surface/view.py').write_text('label = "modelOne"')
            (scan.ROOT / 'surface/app.js.map').write_text('{}')
            self.assertTrue(scan.scan())

if __name__ == '__main__':
    unittest.main()
