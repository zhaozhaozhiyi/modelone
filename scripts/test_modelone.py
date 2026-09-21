"""Regression checks for persisted data and shared configuration (no app startup)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
import sqlalchemy as sa
import yaml

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

    def test_download_filenames_are_branded_and_keep_extensions(self):
        before = brand.BRAND['internal_name']
        try:
            brand.BRAND['internal_name'] = 'modelone'
            self.assertEqual(brand.download_filename('records', 'csv'), 'modelone-records.csv')
            self.assertEqual(brand.download_filename('/tmp/modelone-report.csv', 'csv'), 'modelone-report.csv')
            self.assertEqual(brand.download_filename('workflow.log'), 'modelone-workflow.log')
            self.assertEqual(brand.download_filename('cube-studio.csv'), 'modelone.csv')
            self.assertEqual(brand.download_filename('开源版-report.csv'), 'modelone-当前版本-report.csv')
        finally:
            brand.BRAND['internal_name'] = before

    def test_server_pages_use_the_shared_browser_title(self):
        templates = (
            'myapp/templates/myapp/basic.html',
            'myapp/templates/pods.html',
            'myapp/templates/log.html',
            'myapp/templates/k8s_tail_log.html',
            'myapp/templates/redirect.html',
            'myapp/templates/close.html',
            'myapp/templates/myapp/traceback.html',
        )
        for relative in templates:
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('<title>{{ brand.title }}</title>', text, relative)

    def test_repository_form_uses_shared_registry_default(self):
        source = (ROOT / 'myapp/views/view_images.py').read_text(encoding='utf-8')
        self.assertIn("conf.get('REPOSITORY_ORG') or 'modelone/'", source)
        self.assertNotIn('harbor.oa.com/modelone/', source)

    def test_login_template_is_modelone_branded_and_csrf_ready(self):
        template = (ROOT / 'myapp/templates/appbuilder/general/security/login_db.html').read_text(encoding='utf-8')
        for value in ('{{ brand.title }}', '{{ brand.logo_url }}', '{{ form.hidden_tag() }}',
                      'request.full_path', 'autocomplete="current-password"'):
            self.assertIn(value, template)
        self.assertNotIn('CubeStudio', template)

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

    def test_offline_image_generator_requires_private_registry(self):
        script = ROOT / 'install/kubernetes/all_image.py'
        with tempfile.TemporaryDirectory() as folder:
            env = {key: value for key, value in os.environ.items() if not key.startswith('MODELONE_')}
            missing = subprocess.run(['python3', str(script)], cwd=folder, env=env,
                                     capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn('MODELONE_IMAGE_REGISTRY is required', missing.stderr + missing.stdout)

            env['MODELONE_IMAGE_REGISTRY'] = 'registry.example.test/team'
            generated = subprocess.run(['python3', str(script)], cwd=folder, env=env,
                                       capture_output=True, text=True)
            self.assertEqual(generated.returncode, 0, generated.stderr)
            plan = json.loads((Path(folder) / 'images.json').read_text())
            self.assertTrue(all(row['target'].startswith('registry.example.test/team/modelone/') for row in plan['images']))
            self.assertTrue(all(not row['source'].startswith('modelone/') for row in plan['images']))
            self.assertTrue((Path(folder) / 'push_harbor.sh').exists())

            config = json.loads((ROOT / 'config/modelone.json').read_text())
            config['imageRegistry'] = 'registry.config.example.test/team'
            config_file = Path(folder) / 'modelone.json'
            config_file.write_text(json.dumps(config))
            config_env = {key: value for key, value in env.items() if key != 'MODELONE_IMAGE_REGISTRY'}
            config_env['MODELONE_CONFIG'] = str(config_file)
            configured = subprocess.run(['python3', str(script)], cwd=folder, env=config_env,
                                        capture_output=True, text=True)
            self.assertNotEqual(configured.returncode, 0, 'The image output directory must not be reused')
            with tempfile.TemporaryDirectory() as configured_folder:
                configured = subprocess.run(['python3', str(script)], cwd=configured_folder, env=config_env,
                                            capture_output=True, text=True)
                self.assertEqual(configured.returncode, 0, configured.stderr)
                configured_plan = json.loads((Path(configured_folder) / 'images.json').read_text())
                self.assertTrue(all(row['target'].startswith('registry.config.example.test/team/modelone/')
                                    for row in configured_plan['images']))

    def test_release_and_resource_gates_require_enterprise_inputs(self):
        config_path = ROOT / 'config/modelone.json'
        render_script = ROOT / 'scripts/render_deployment.py'
        inventory_script = ROOT / 'scripts/resource_inventory.py'
        with tempfile.TemporaryDirectory() as folder:
            config = json.loads(config_path.read_text())
            for key in ('imageRegistry', 'assetBaseUrl', 'copyrightHolder', 'helpUrl', 'supportUrl', 'termsUrl', 'privacyUrl'):
                config[key] = ''
            config_file = Path(folder) / 'modelone.json'
            config_file.write_text(json.dumps(config))
            env = {key: value for key, value in os.environ.items() if not key.startswith('MODELONE_')}
            env['MODELONE_CONFIG'] = str(config_file)
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--output', str(Path(folder) / 'release')],
                cwd=ROOT, env=env, capture_output=True, text=True
            )
            self.assertNotEqual(rendered.returncode, 0)
            self.assertIn('asset_base_url', rendered.stderr + rendered.stdout)
            inventoried = subprocess.run(
                ['python3', str(inventory_script), '--require-complete', '--output', str(Path(folder) / 'inventory.json')],
                cwd=ROOT, env=env, capture_output=True, text=True
            )
            self.assertNotEqual(inventoried.returncode, 0)
            self.assertIn('image_registry', inventoried.stderr + inventoried.stdout)

    def test_release_compose_is_portable_and_images_include_job_templates(self):
        render_script = ROOT / 'scripts/render_deployment.py'
        with tempfile.TemporaryDirectory() as folder:
            env = {key: value for key, value in os.environ.items() if not key.startswith('MODELONE_')}
            env.update({
                'MODELONE_IMAGE_REGISTRY': 'registry.example.test/team',
                'MODELONE_ASSET_BASE_URL': 'https://assets.example.test/modelone',
                'MODELONE_COPYRIGHT_HOLDER': 'Validation Company',
                'MODELONE_HELP_URL': 'https://help.example.test/modelone',
                'MODELONE_SUPPORT_URL': 'https://support.example.test/modelone',
                'MODELONE_TERMS_URL': 'https://www.example.test/modelone/terms',
                'MODELONE_PRIVACY_URL': 'https://www.example.test/modelone/privacy',
            })
            output = Path(folder) / 'release'
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--output', str(output)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            compose = yaml.safe_load((output / 'compose.yaml').read_text())
            self.assertEqual(compose['services']['mysql']['volumes'], [
                'modelone-mysql-data:/var/lib/mysql',
            ])
            self.assertEqual(compose['services']['frontend']['volumes'], [])
            self.assertEqual(compose['services']['myapp']['volumes'], [
                'modelone-kubeflow-data:/data/k8s/kubeflow',
                '${MODELONE_KUBECONFIG:-./kubeconfig}:/home/myapp/kubeconfig:ro',
            ])
            self.assertNotIn(str(ROOT), (output / 'compose.yaml').read_text())
            self.assertIn('COPY job-template /cube-studio/job-template',
                          (ROOT / 'install/docker/Dockerfile').read_text())

    def test_scan_blocks_legacy_text_and_maps(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('scan', ROOT / 'scripts/brand_scan.py')
        scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
        self.assertIn('myapp/frontend/public', scan.SURFACES)
        self.assertIn('myapp/vision/public', scan.SURFACES)
        self.assertIn('myapp/visionPlus/public', scan.SURFACES)
        self.assertIn('myapp/static/assets/modelone', scan.SURFACES)
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

    def test_artifact_scan_allows_mount_compatibility_but_blocks_legacy_hosts(self):
        spec = importlib.util.spec_from_file_location('artifact_scan', ROOT / 'scripts/brand_scan.py')
        scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
        with tempfile.TemporaryDirectory() as folder:
            artifact = Path(folder) / 'kubernetes.yaml'
            artifact.write_text('volume: /cube-studio/aihub\nimage: registry.example.test/team/modelone/app:v1\n')
            self.assertFalse(scan.scan_artifacts([artifact]))
            artifact.write_text('image: ccr.ccs.tencentyun.com/cube-argoproj/workflow:v3.4.3\n')
            self.assertTrue(scan.scan_artifacts([artifact]))
            artifact.write_text('label: Cube Studio\n')
            self.assertTrue(scan.scan_artifacts([artifact]))
            artifact.with_suffix('.map').write_text('{}')
            self.assertTrue(scan.scan_artifacts([artifact.with_suffix('.map')]))

    def test_job_template_scan_allows_only_documented_compatibility_alias(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('scan_job', ROOT / 'scripts/brand_scan.py')
        scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
        with tempfile.TemporaryDirectory() as folder:
            scan.ROOT = Path(folder); scan.SURFACES = ('job-template',); scan.BUILDS = ()
            target = scan.ROOT / 'job-template/job/dataset'
            target.mkdir(parents=True)
            path = target / 'launcher.py'
            path.write_text("if args.src_type in ('modelone', 'cube-studio', '当前平台'):\n")
            self.assertFalse(scan.scan())
            path.write_text("label = 'Cube Studio'\n")
            self.assertTrue(scan.scan())

    def test_repository_remote_setup_is_explicit_and_read_only_upstream(self):
        spec = importlib.util.spec_from_file_location('remotes', ROOT / 'scripts/configure_modelone_remotes.py')
        remotes = importlib.util.module_from_spec(spec); spec.loader.exec_module(remotes)
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            actions = remotes.configure(
                repo,
                'https://git.example.test/modelone/platform.git',
                'https://git.example.test/source/cube-studio.git',
                apply=True,
            )
            self.assertEqual(len(actions), 3)
            self.assertEqual(remotes.remote_url(repo, 'origin'), 'https://git.example.test/modelone/platform.git')
            self.assertEqual(remotes.remote_url(repo, 'upstream'), 'https://git.example.test/source/cube-studio.git')
            self.assertEqual(remotes.remote_url(repo, 'upstream', push=True), 'DISABLED')
            with self.assertRaises(ValueError):
                remotes.configure(repo, 'https://other.example.test/modelone.git', apply=True)
            with self.assertRaises(ValueError):
                remotes.configure(repo, 'https://user:password@git.example.test/modelone.git')

if __name__ == '__main__':
    unittest.main()
