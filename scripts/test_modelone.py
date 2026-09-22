"""Regression checks for persisted data and shared configuration (no app startup)."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
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
        self.assertEqual(scripts.get_heads(), ['modelone_space_type_20260922'])
        revisions = list(scripts.iterate_revisions('head', '40e1215ccbd6'))
        self.assertEqual([r.revision for r in revisions], ['modelone_space_type_20260922', 'modelone_brand_links_20260921', 'modelone_brand_20260921'])

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

    def test_legacy_mnist_host_moves_to_owned_asset_path(self):
        before = dict(brand.BRAND)
        try:
            brand.BRAND.update(asset_base_url='https://assets.example.test/modelone')
            legacy = 'https://docker-76009.sz.gfp.tencent-cloud.com/kubeflow/pytorch/example/data/train-images-idx3-ubyte.gz'
            self.assertEqual(
                brand.resolve_resources(legacy),
                'https://assets.example.test/modelone/datasets/mnist/train-images-idx3-ubyte.gz',
            )
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

    def test_legacy_theme_examples_use_the_shared_brand_name(self):
        for relative in ('myapp/templates/myapp/theme.html', 'myapp/templates/myapp/paper-theme.html'):
            text = (ROOT / relative).read_text(encoding='utf-8')
            self.assertIn('{{ brand.name }}', text, relative)
            self.assertNotRegex(text, r'ForkedCosmo|Bootstrap theme|Project name|>Brand<')

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

    def test_frontend_theme_uses_configured_primary_color(self):
        source = (ROOT / 'myapp/frontend/src/theme.ts').read_text(encoding='utf-8')
        self.assertIn("import { brand } from './brand';", source)
        self.assertIn('brand.primaryColor', source)
        self.assertIn('brand.secondaryColor', source)
        self.assertIn("'--ant-primary-color': primary", source)

    def test_editor_themes_use_configured_brand_palette(self):
        for app in ('vision', 'visionPlus'):
            source = (ROOT / 'myapp' / app / 'src/index.tsx').read_text(encoding='utf-8')
            brand = (ROOT / 'myapp' / app / 'src/brand.ts').read_text(encoding='utf-8')
            self.assertIn("brandPalette", source, app)
            self.assertIn("brandFontFamily", source, app)
            self.assertIn('primaryColor', brand, app)
            self.assertNotIn('#015cda', source + brand, app)

    def test_runtime_brand_script_updates_browser_theme_color(self):
        source = (ROOT / 'scripts/generate_brand.py').read_text(encoding='utf-8')
        self.assertIn("meta[name=\"theme-color\"]", source)
        self.assertIn("link[rel=\"apple-touch-icon\"]", source)
        self.assertIn('themeColor.content = b.primaryColor', source)
        self.assertIn("--mo-brand-secondary", source)

    def test_pwa_manifest_uses_shared_brand_tokens(self):
        before = dict(brand.BRAND)
        try:
            brand.BRAND.update(
                name='Acme modelOne',
                title='Acme modelOne｜AI 平台',
                description='Acme 企业级 AI 平台',
                favicon_url='https://cdn.example.test/modelone/icon.svg',
                primary_color='#102030',
                login_background_color='#f0f2f4',
            )
            manifest = brand.public_manifest()
            self.assertEqual(manifest['short_name'], 'Acme modelOne')
            self.assertEqual(manifest['name'], 'Acme modelOne｜AI 平台')
            self.assertEqual(manifest['description'], 'Acme 企业级 AI 平台')
            self.assertEqual(manifest['icons'][0]['src'], 'https://cdn.example.test/modelone/icon.svg')
            self.assertEqual(manifest['theme_color'], '#102030')
            self.assertEqual(manifest['background_color'], '#f0f2f4')
        finally:
            brand.BRAND.clear()
            brand.BRAND.update(before)

        for app in ('frontend', 'vision', 'visionPlus'):
            manifest = json.loads((ROOT / 'myapp' / app / 'public/manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['name'], brand.BRAND['title'], app)
            self.assertEqual(manifest['theme_color'], brand.BRAND['primary_color'], app)
            self.assertEqual(manifest['background_color'], brand.BRAND['login_background_color'], app)
            self.assertEqual(manifest['icons'][0]['src'], 'modelone-mark.svg', app)

    def test_login_and_error_templates_use_configured_visual_tokens(self):
        login = (ROOT / 'myapp/templates/appbuilder/general/security/login_db.html').read_text(encoding='utf-8')
        error = (ROOT / 'myapp/templates/modelone-error.html').read_text(encoding='utf-8')
        for value in ('brand.secondary_color', 'brand.login_background_color', 'brand.login_surface_color'):
            self.assertIn(value, login)
        for value in ('brand.secondary_color', 'brand.login_background_color', 'brand.font_family'):
            self.assertIn(value, error)

    def test_manifest_icon_type_matches_configured_asset(self):
        for url, expected in (
            ('https://cdn.example.test/icon.PNG?version=2', 'image/png'),
            ('/static/icon.ico', 'image/x-icon'),
            ('/static/icon.svg', 'image/svg+xml'),
            ('https://cdn.example.test/icon', None),
        ):
            with self.subTest(url=url), patch.dict(brand.BRAND, favicon_url=url):
                icon = brand.public_manifest()['icons'][0]
                self.assertEqual(icon.get('type'), expected)
                self.assertEqual(icon.get('sizes'), 'any' if expected == 'image/svg+xml' else None)

    def test_proxy_error_pages_use_escaped_brand_config_without_backend_assets(self):
        with patch.dict(brand.BRAND, title='modelOne <Operations>', copyright='Copyright © Validation & Co',
                        primary_color='#123456', support_url='https://support.example.test/?a=1&b=2'):
            pages = brand.proxy_error_pages()
            self.assertEqual(set(pages), {'500.html', '502.html', '503.html', '504.html'})
            for name, html in pages.items():
                self.assertIn('<title>modelOne &lt;Operations&gt;</title>', html)
                self.assertIn('Copyright © Validation &amp; Co', html)
                self.assertIn('https://support.example.test/?a=1&amp;b=2', html)
                self.assertIn('<p class="code">' + name[:3] + '</p>', html)
                self.assertIn('--ink: #123456', html)
                self.assertIn('"PingFang SC"', html)
                self.assertNotIn('&#34;', html)
                self.assertNotIn('<script', html)
        with patch.dict(brand.BRAND, support_url='', copyright=''):
            html = brand.proxy_error_pages()['502.html']
            self.assertNotIn('联系技术支持', html)
            self.assertNotIn('<footer>', html)

    def test_public_manifest_routes_follow_runtime_brand_and_application_scope(self):
        from flask import Flask
        app = Flask('modelone-brand-test')
        load('brand_web').register_brand_routes(app, brand)
        client = app.test_client()
        with patch.dict(brand.BRAND, title='modelOne｜Runtime', primary_color='#123456',
                        login_background_color='#e1e2e3', image_registry='private-registry.test/team',
                        tls_secret_name='private-tls-name'):
            for app_name, scope in brand.BROWSER_APPS.items():
                response = client.get('/myapp/manifest/' + app_name + '.json')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.mimetype, 'application/manifest+json')
                self.assertEqual(response.headers['Cache-Control'], 'no-store')
                manifest = response.get_json()
                self.assertEqual(manifest['name'], 'modelOne｜Runtime')
                self.assertEqual(manifest['theme_color'], '#123456')
                self.assertEqual(manifest['background_color'], '#e1e2e3')
                self.assertEqual(manifest['start_url'], scope)
                self.assertEqual(manifest['id'], scope)
                self.assertEqual(manifest['scope'], scope)
                self.assertEqual(manifest['icons'][0]['src'], '/static/assets/modelone/modelone-mark.svg')
            script = client.get('/myapp/brand.js')
            self.assertEqual(script.status_code, 200)
            self.assertEqual(script.headers['Cache-Control'], 'no-store')
            self.assertNotIn('private-registry', script.text)
            self.assertNotIn('private-tls-name', script.text)
        self.assertEqual(client.get('/myapp/manifest/unknown.json').status_code, 404)

    def test_brand_css_values_are_validated(self):
        original_path = brand.CONFIG_PATH
        try:
            with tempfile.TemporaryDirectory() as folder:
                config = json.loads((ROOT / 'config/modelone.json').read_text(encoding='utf-8'))
                path = Path(folder) / 'modelone.json'
                config['primaryColor'] = '#17191d; color: red'
                path.write_text(json.dumps(config), encoding='utf-8')
                brand.CONFIG_PATH = path
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['primaryColor'] = '#17191d'
                config['secondaryColor'] = '#12345'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['secondaryColor'] = '#3b82f6'
                config['fontFamily'] = 'Inter; body{display:none}'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['fontFamily'] = 'Inter,\nbody{display:none}'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['fontFamily'] = '思源黑体, Microsoft YaHei, sans-serif'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True):
                    self.assertEqual(brand.load_brand()['font_family'], config['fontFamily'])
                for color in ('#abc', '#abcd', '#aabbcc', '#aabbccdd'):
                    config['primaryColor'] = color
                    path.write_text(json.dumps(config), encoding='utf-8')
                    with patch.dict(os.environ, {}, clear=True):
                        self.assertEqual(brand.load_brand()['primary_color'], color)
                config['primaryColor'] = '#12345'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['primaryColor'] = '#17191d'
                config['publicDomain'] = 'modelone.example.test'
                config['tlsSecretName'] = 'modelone-tls'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True):
                    loaded = brand.load_brand()
                    self.assertEqual(loaded['public_domain'], 'modelone.example.test')
                    self.assertEqual(loaded['tls_secret_name'], 'modelone-tls')
                config['publicDomain'] = 'https://modelone.example.test'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
                config['publicDomain'] = ''
                config['tlsSecretName'] = 'modelone-tls'
                path.write_text(json.dumps(config), encoding='utf-8')
                with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                    brand.load_brand()
        finally:
            brand.CONFIG_PATH = original_path

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
            blank_config = json.loads((ROOT / 'config/modelone.json').read_text())
            blank_config['imageRegistry'] = ''
            blank_file = Path(folder) / 'blank-modelone.json'
            blank_file.write_text(json.dumps(blank_config))
            env['MODELONE_CONFIG'] = str(blank_file)
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
            with tempfile.TemporaryDirectory() as manifest_folder:
                rooted = subprocess.run([
                    'python3', str(script), '--manifest-root', str(ROOT / 'install/kubernetes'),
                    '--output', manifest_folder,
                ], cwd=ROOT, env=env, capture_output=True, text=True)
                self.assertEqual(rooted.returncode, 0, rooted.stderr)
                rooted_plan = json.loads((Path(manifest_folder) / 'images.json').read_text())
                self.assertIn('nginx', {row['runtime'] for row in rooted_plan['images']})

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
        image_script = ROOT / 'install/kubernetes/all_image.py'
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
            image_output = Path(folder) / 'images'
            planned = subprocess.run(
                ['python3', str(image_script), '--manifest-root', str(ROOT / 'install/kubernetes'),
                 '--output', str(image_output)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            output = Path(folder) / 'release'
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--image-plan',
                 str(image_output / 'images.json'), '--output', str(output)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            compose = yaml.safe_load((output / 'compose.yaml').read_text())
            self.assertEqual(compose['services']['mysql']['volumes'], [
                'modelone-mysql-data:/var/lib/mysql',
            ])
            self.assertEqual(compose['services']['frontend']['volumes'], [
                './frontend-errors:/data/web/static/modelone-errors:ro',
            ])
            manifests = list(yaml.safe_load_all((output / 'kubernetes.yaml').read_text()))
            errors = next(doc for doc in manifests if doc['metadata']['name'] == 'modelone-error-pages')
            self.assertEqual(errors['kind'], 'ConfigMap')
            for filename, html in errors['data'].items():
                self.assertEqual((output / 'frontend-errors' / filename).read_text(), html)
                self.assertIn('Validation Company', html)
                self.assertIn('https://support.example.test/modelone', html)
            frontend = next(doc for doc in manifests if doc['kind'] == 'Deployment'
                            and doc['metadata']['name'] == 'kubeflow-dashboard-frontend')['spec']['template']['spec']
            self.assertIn({'name': 'modelone-error-pages', 'configMap': {'name': 'modelone-error-pages'}}, frontend['volumes'])
            self.assertIn({'name': 'modelone-error-pages', 'mountPath': '/data/web/static/modelone-errors',
                           'readOnly': True}, frontend['containers'][0]['volumeMounts'])
            self.assertEqual(compose['services']['myapp']['volumes'], [
                'modelone-kubeflow-data:/data/k8s/kubeflow',
                '${MODELONE_KUBECONFIG:-./kubeconfig}:/home/myapp/kubeconfig:ro',
            ])
            self.assertNotIn(str(ROOT), (output / 'compose.yaml').read_text())
            self.assertIn('COPY job-template /cube-studio/job-template',
                          (ROOT / 'install/docker/Dockerfile').read_text())

    def test_release_requires_an_image_plan(self):
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
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--output', str(Path(folder) / 'release')],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(rendered.returncode, 0)
            self.assertIn('--image-plan', rendered.stderr + rendered.stdout)

    def test_release_rejects_an_image_plan_for_another_registry(self):
        render_script = ROOT / 'scripts/render_deployment.py'
        image_script = ROOT / 'install/kubernetes/all_image.py'
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
            image_output = Path(folder) / 'images'
            planned = subprocess.run(
                ['python3', str(image_script), '--manifest-root', str(ROOT / 'install/kubernetes'),
                 '--output', str(image_output)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan_path = image_output / 'images.json'
            plan = json.loads(plan_path.read_text())
            plan['registry'] = 'registry.other.example/team'
            plan_path.write_text(json.dumps(plan))
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--image-plan', str(plan_path),
                 '--output', str(Path(folder) / 'release')],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(rendered.returncode, 0)
            self.assertIn('registry', rendered.stderr + rendered.stdout)

    def test_release_rejects_targets_outside_the_configured_registry(self):
        render_script = ROOT / 'scripts/render_deployment.py'
        image_script = ROOT / 'install/kubernetes/all_image.py'
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
            image_output = Path(folder) / 'images'
            planned = subprocess.run(
                ['python3', str(image_script), '--manifest-root', str(ROOT / 'install/kubernetes'),
                 '--output', str(image_output)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(planned.returncode, 0, planned.stderr)
            plan_path = image_output / 'images.json'
            plan = json.loads(plan_path.read_text())
            plan['images'][0]['target'] = 'registry.other.example/team/modelone/foreign:v1'
            plan_path.write_text(json.dumps(plan))
            rendered = subprocess.run(
                ['python3', str(render_script), '--release', '--image-plan', str(plan_path),
                 '--output', str(Path(folder) / 'release')],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertNotEqual(rendered.returncode, 0)
            self.assertIn('outside MODELONE_IMAGE_REGISTRY', rendered.stderr + rendered.stdout)

    def test_scan_blocks_legacy_text_and_maps(self):
        import tempfile
        spec = importlib.util.spec_from_file_location('scan', ROOT / 'scripts/brand_scan.py')
        scan = importlib.util.module_from_spec(spec); spec.loader.exec_module(scan)
        self.assertIn('myapp/frontend/public', scan.SURFACES)
        self.assertIn('myapp/vision/public', scan.SURFACES)
        self.assertIn('myapp/visionPlus/public', scan.SURFACES)
        self.assertIn('config/modelone.json', scan.SURFACES)
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
            artifact.write_text('resolver: ccr.ccs.tencentyun.com\n')
            self.assertTrue(scan.scan_artifacts([artifact]))
            artifact.write_text('image: registry.example.test/team/modelone/third-party/ccr.ccs.tencentyun.com/argoproj/workflow:v3.4.3\n')
            self.assertFalse(scan.scan_artifacts([artifact]))
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

    def test_cluster_entrypoints_require_rendered_release_manifests(self):
        for name in ('start.sh', 'start-with-kubesphere.sh'):
            source = (ROOT / 'install/kubernetes' / name).read_text(encoding='utf-8')
            self.assertIn('modelone-manifests.sh', source)
            self.assertIn('kubectl apply -f "$MODELONE_KUBERNETES_MANIFEST"', source)
            self.assertIn('MODELONE_SERVICE_EXTERNAL_IP', source)
            self.assertIn('cd "$MODELONE_SOURCE_ROOT"', source)
            self.assertNotIn('kubectl apply -k cube/overlays', source)
            self.assertNotIn('kubectl apply -f argo/install-3.4.3-all.yaml', source)
        helper = (ROOT / 'install/kubernetes/modelone-manifests.sh').read_text(encoding='utf-8')
        self.assertIn('MODELONE_MANIFEST_ROOT', helper)
        self.assertIn('modelone_manifest', helper)
        self.assertIn('modelone_kustomize', helper)
        self.assertIn('command kubectl', helper)
        for path in ('install/kubernetes/cube/overlays/config/config.py', 'install/docker/config.py'):
            source = (ROOT / path).read_text(encoding='utf-8')
            self.assertIn('MODELONE_SERVICE_EXTERNAL_IP', source)
        offline = (ROOT / 'install/kubernetes/offline.md').read_text(encoding='utf-8')
        self.assertIn('MODELONE_ASSET_BASE_URL', offline)
        self.assertNotIn('ccr.ccs.tencentyun.com', offline)
        self.assertNotIn('docker-76009.sz.gfp.tencent-cloud.com', offline)

if __name__ == '__main__':
    unittest.main()

class SpaceTypeMigrationTests(unittest.TestCase):
    """Single-layer workspace rewrite: idempotent upgrade, exact downgrade."""

    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            'space_migration', ROOT / 'myapp/migrations/versions/modelone_space_type_20260922.py')
        self.migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.migration)
        self.engine = sa.create_engine('sqlite://')
        with self.engine.begin() as connection:
            connection.execute(sa.text('CREATE TABLE project (id INTEGER PRIMARY KEY, type VARCHAR(50), expand TEXT)'))
            connection.execute(sa.text('CREATE TABLE project_user (id INTEGER PRIMARY KEY, project_id INTEGER)'))
            connection.execute(sa.text('CREATE TABLE notebook (id INTEGER PRIMARY KEY, project_id INTEGER)'))
            connection.execute(sa.text("INSERT INTO project VALUES (1, 'org', '{\"cluster\": \"dev\"}')"))
            connection.execute(sa.text("INSERT INTO project VALUES (2, NULL, '{}')"))
            connection.execute(sa.text("INSERT INTO project VALUES (3, NULL, '{}')"))
            connection.execute(sa.text("INSERT INTO project VALUES (4, 'job-template', '{}')"))
            connection.execute(sa.text("INSERT INTO project VALUES (5, 'space', '{}')"))
            connection.execute(sa.text('INSERT INTO project_user VALUES (1, 1)'))
            connection.execute(sa.text('INSERT INTO notebook VALUES (1, 2)'))

    def types(self):
        with self.engine.connect() as connection:
            return {row[0]: row[1] for row in
                    connection.execute(sa.text('SELECT id, type FROM project ORDER BY id'))}

    def expands(self):
        with self.engine.connect() as connection:
            return {row[0]: row[1] for row in
                    connection.execute(sa.text('SELECT id, expand FROM project ORDER BY id'))}

    def test_upgrade_rewrite_is_idempotent_and_downgrade_restores(self):
        with self.engine.begin() as connection:
            changed = self.migration.upgrade_tables(connection)
        self.assertEqual(changed, 2, 'org row and referenced untyped row must become spaces')
        self.assertEqual(self.types(), {1: 'space', 2: 'space', 3: None, 4: 'job-template', 5: 'space'})
        expand = json.loads(self.expands()[1])
        self.assertEqual(expand.get('cluster'), 'dev', 'Existing expand keys must survive')
        self.assertEqual(expand.get('_mo_space_from'), 'org')
        with self.engine.begin() as connection:
            self.assertEqual(self.migration.upgrade_tables(connection), 0, 'Upgrade must be idempotent')
        with self.engine.begin() as connection:
            restored = self.migration.downgrade_tables(connection)
        self.assertEqual(restored, 2)
        self.assertEqual(self.types(), {1: 'org', 2: None, 3: None, 4: 'job-template', 5: 'space'})
        self.assertNotIn('_mo_space_from', json.loads(self.expands()[1]))
        self.assertEqual(json.loads(self.expands()[1]).get('cluster'), 'dev')

    def test_migration_head_includes_space_revision(self):
        from alembic.script import ScriptDirectory
        scripts = ScriptDirectory(str(ROOT / 'myapp/migrations'))
        self.assertEqual(scripts.get_heads(), ['modelone_space_type_20260922'])
