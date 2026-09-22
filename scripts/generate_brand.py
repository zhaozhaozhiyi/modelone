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
  var touchIcon = document.querySelector('link[rel="apple-touch-icon"]');
  if (touchIcon && b.faviconUrl) touchIcon.href = b.faviconUrl;
  var description = document.querySelector('meta[name="description"]');
  if (description) description.content = b.description;
  var themeColor = document.querySelector('meta[name="theme-color"]');
  if (themeColor && b.primaryColor) themeColor.content = b.primaryColor;
  document.documentElement.style.setProperty('--mo-brand-primary', b.primaryColor);
  document.documentElement.style.setProperty('--mo-brand-secondary', b.secondaryColor);
  document.documentElement.style.setProperty('--mo-login-background', b.loginBackgroundColor);
  document.documentElement.style.setProperty('--mo-login-surface', b.loginSurfaceColor);
  document.documentElement.style.setProperty('--mo-font-sans', b.fontFamily);
};
window.applyModeloneBrand();
'''
    for app in ('frontend', 'vision', 'visionPlus'):
        public = ROOT / 'myapp' / app / 'public'
        (public / 'brand-config.js').write_text(script, encoding='utf-8')
        (public / 'manifest.json').write_text(
            json.dumps(brand.public_manifest(), ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
    errors = ROOT / 'myapp/static/modelone-errors'
    errors.mkdir(parents=True, exist_ok=True)
    for filename, html in brand.proxy_error_pages().items():
        (errors / filename).write_text(html, encoding='utf-8')
    print('Generated brand defaults for all three frontends and standalone proxy errors')
