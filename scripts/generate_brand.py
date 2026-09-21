#!/usr/bin/env python3
"""Generate browser defaults from the same config used by backend containers."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modelone_brand', ROOT / 'myapp/brand.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

if __name__ == '__main__':
    config = brand.public_brand()
    config['faviconUrl'] = config['faviconUrl'] or '/static/assets/modelone/modelone-mark.svg'
    script = 'window.MODELONE_BRAND = ' + json.dumps(config, ensure_ascii=True) + ';\n'
    script += '''window.applyModeloneBrand = function () {
  var b = window.MODELONE_BRAND;
  document.title = b.title;
  var icon = document.querySelector('link[rel="icon"]');
  if (icon && b.faviconUrl) icon.href = b.faviconUrl;
  var description = document.querySelector('meta[name="description"]');
  if (description) description.content = b.description;
  document.documentElement.style.setProperty('--mo-brand-primary', b.primaryColor);
  document.documentElement.style.setProperty('--mo-font-sans', b.fontFamily);
};
window.applyModeloneBrand();
'''
    for app in ('frontend', 'vision', 'visionPlus'):
        public = ROOT / 'myapp' / app / 'public'
        (public / 'brand-config.js').write_text(script, encoding='utf-8')
    print('Generated brand defaults for all three frontends')
