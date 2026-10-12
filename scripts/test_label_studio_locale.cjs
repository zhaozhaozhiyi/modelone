const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createRequire } = require('node:module');

const root = path.resolve(__dirname, '..');
const { JSDOM } = createRequire(path.join(root, 'myapp/frontend/package.json'))('jsdom');
const source = fs.readFileSync(path.join(root, 'integrations/label-studio/locale-zh.js'), 'utf8');

async function main() {
  const dom = new JSDOM('<!doctype html><html><body></body></html>', {
    runScripts: 'outside-only',
    url: 'http://localhost/labelstudio/projects',
  });

  try {
    const { document, Node } = dom.window;
    const label = document.createElement('span');
    const firstTextNode = document.createTextNode('Create Pro');
    const secondTextNode = document.createTextNode('ject');
    label.append(firstTextNode, secondTextNode);
    document.body.append(label);

    dom.window.eval(source);
    await new Promise((resolve) => document.addEventListener('DOMContentLoaded', resolve, { once: true }));

    assert.equal(label.textContent, '创建项目');
    assert.equal(firstTextNode.parentNode, label);
    assert.equal(secondTextNode.parentNode, label);
    assert.equal(secondTextNode.nodeValue, '');

    const inserted = document.createTextNode('New');
    assert.doesNotThrow(() => label.insertBefore(inserted, firstTextNode));
    assert.equal(label.firstChild, inserted);
    console.log('PASS: translated React text nodes remain valid insertion anchors');
  } finally {
    dom.window.close();
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
