// Execute the actual default and runtime scripts against each built document.
// JSDOM comes from the frontend's installed Jest dependencies; no network used.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');
const { execFileSync } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const { JSDOM } = createRequire(path.join(root, 'myapp/frontend/package.json'))('jsdom');
const runtime = execFileSync('python3', ['-c', [
  'import importlib.util',
  "spec = importlib.util.spec_from_file_location('brand', 'myapp/brand.py')",
  'brand = importlib.util.module_from_spec(spec)',
  'spec.loader.exec_module(brand)',
  'print(brand.browser_config_script())',
].join('\n')], {
  cwd: root, encoding: 'utf8',
  env: { ...process.env, MODELONE_TITLE: 'modelOne｜Runtime', MODELONE_PRIMARY_COLOR: '#123456',
    MODELONE_FAVICON_URL: 'https://assets.example.test/runtime.png' },
});

for (const [app, folder, base] of [
  ['frontend', 'frontend', '/frontend/'],
  ['vision', 'vison', '/static/appbuilder/vison/'],
  ['visionPlus', 'visonPlus', '/static/appbuilder/visonPlus/'],
]) {
  const output = path.join(root, 'myapp/static/appbuilder', folder);
  const dom = new JSDOM(fs.readFileSync(path.join(output, 'index.html'), 'utf8'), {
    url: 'https://modelone.example.test' + base, runScripts: 'outside-only',
  });
  try {
    const doc = dom.window.document;
    const manifest = doc.querySelector('link[rel="manifest"]');
    dom.window.eval(fs.readFileSync(path.join(output, 'brand-config.js'), 'utf8'));
    // An unavailable backend leaves the standalone build manifest intact.
    assert.equal(manifest.href, 'https://modelone.example.test' + base + 'manifest.json');
    assert.equal(manifest.dataset.modeloneApp, app);
    dom.window.eval(runtime);
    assert.equal(doc.title, 'modelOne｜Runtime');
    assert.equal(doc.querySelector('meta[name="theme-color"]').content, '#123456');
    assert.equal(doc.querySelector('link[rel="icon"]').href, 'https://assets.example.test/runtime.png');
    assert.equal(manifest.href, 'https://modelone.example.test/myapp/manifest/' + app + '.json');
    dom.window.eval(runtime);
    assert.equal(doc.querySelectorAll('link[rel="manifest"]').length, 1);
    assert.equal(manifest.href, 'https://modelone.example.test/myapp/manifest/' + app + '.json');
    console.log('PASS: ' + app + ' static fallback and runtime brand/manifest update');
  } finally {
    dom.window.close();
  }
}
