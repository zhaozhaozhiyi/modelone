#!/usr/bin/env python3
"""Generate browser defaults from the same config used by backend containers."""
import importlib.util
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE_VERSION = '20261010-ai-platform'
spec = importlib.util.spec_from_file_location('modelone_brand', ROOT / 'myapp/brand.py')
brand = importlib.util.module_from_spec(spec)
spec.loader.exec_module(brand)

if __name__ == '__main__':
    config = brand.public_brand()
    config['faviconUrl'] = config['faviconUrl'] or '/static/assets/modelone/modelone-mark.svg?v=' + CACHE_VERSION
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
    for app, output in (
        ('frontend', 'frontend'),
        ('vision', 'vison'),
        ('visionPlus', 'visonPlus'),
    ):
        built = ROOT / 'myapp/static/appbuilder' / output
        if built.is_dir():
            (built / 'brand-config.js').write_text(script, encoding='utf-8')
            (built / 'manifest.json').write_text(
                json.dumps(brand.public_manifest(app), ensure_ascii=False, indent=2) + '\n',
                encoding='utf-8',
            )
            index = built / 'index.html'
            if index.is_file():
                source = index.read_text(encoding='utf-8')
                pattern = r'((?:%PUBLIC_URL%/|\./|/frontend/|/static/appbuilder/(?:vison|visonPlus)/)?modelone-mark\.svg)(?:\?[^"\']*)?'
                source = re.sub(pattern, r'\1?v=' + CACHE_VERSION, source)
                source = re.sub(
                    r'(<title>).*?(</title>)',
                    lambda match: match.group(1) + html.escape(brand.BRAND['title']) + match.group(2),
                    source,
                    count=1,
                )
                source = re.sub(
                    r'(<meta\s+name="description"\s+content=")[^"]*(")',
                    lambda match: match.group(1) + html.escape(brand.BRAND['description'], quote=True) + match.group(2),
                    source,
                    count=1,
                )
                index.write_text(source, encoding='utf-8')
    errors = ROOT / 'myapp/static/modelone-errors'
    errors.mkdir(parents=True, exist_ok=True)
    for filename, html in brand.proxy_error_pages().items():
        (errors / filename).write_text(html, encoding='utf-8')
    print('Generated brand defaults for all three frontends and standalone proxy errors')
