#!/usr/bin/env python3
"""Release gate for product sources and compiled bundles; licenses stay in source."""
import argparse
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SURFACES = ('myapp/frontend/public', 'myapp/frontend/src', 'myapp/vision/public', 'myapp/vision/src', 'myapp/visionPlus/public', 'myapp/visionPlus/src', 'myapp/templates', 'myapp/init', 'myapp/example', 'myapp/views', 'myapp/models', 'myapp/cli.py', 'install/kubernetes/all_image.py')
BUILDS = ('myapp/static/appbuilder/frontend', 'myapp/static/appbuilder/vison', 'myapp/static/appbuilder/visonPlus')
DOCUMENTATION = ('job-template/**/*.md', 'images/**/*.md', 'install/**/*.md')
OLD = re.compile(r'cube[-_ ]?studio|开源版|商业版|开源社区|data-master\.net|/vison(?:Plus)?/logo\.png|cubeStudioLogo|logoCB', re.I)
HOSTS = re.compile(r'cube-studio\.oss-cn-hangzhou\.aliyuncs\.com|ccr\.ccs\.tencentyun\.com/cube-studio|(?:github\.com|githubfast\.com)/data-infra/(?:cube-studio|modelone)', re.I)
# Compatibility exceptions are syntactic tokens, not blanket file exclusions.
TECHNICAL = (
    re.compile(r'\bcubestudio(?:\.[A-Za-z_][\w]*)+'),  # existing Python SDK imports
    re.compile(r'/(?:[^\s"\']*/)?cube-studio(?:/[^\s"\']*)?'),  # mounted paths
    re.compile(r'(?<=activate )cube-studio\b'),  # existing conda environment
    re.compile(r'(?<="name": ")cube-studio(?=")'),  # kernelspec identifier
    re.compile(r'(?<=python310,)cube-studio(?=\))'),
    re.compile(r"(?<=filter_by\(name=')cube-studio(?='\))"),  # upgrade-only alias
)

def scan(include_build=False):
    failures = []
    paths = [path for pattern in DOCUMENTATION for path in ROOT.glob(pattern) if path.is_file()]
    for item in SURFACES + (BUILDS if include_build else ()):
        root = ROOT / item
        if not root.exists():
            failures.append(item + ': missing release surface')
            continue
        paths.extend([root] if root.is_file() else sorted(p for p in root.rglob('*') if p.is_file()))
    for path in paths:
        if path.suffix in ('.map',):
            failures.append(str(path.relative_to(ROOT)) + ': source map must not be published')
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            continue
        for number, line in enumerate(content.splitlines(), 1):
            # Build maps referenced by JS/CSS are forbidden even if a map is missing.
            issue = bool(re.search(r'^[ \t]*(?://[#@]|/\*[#@])\s*sourceMappingURL=', line))
            safe = line
            if '/example/' in str(path) or path.name == 'cli.py':
                for expression in TECHNICAL:
                    safe = expression.sub('', safe)
            if HOSTS.search(line) or OLD.search(safe) or issue:
                failures.append('%s:%s: %s' % (path.relative_to(ROOT), number, line.strip()[:180]))
    return failures

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--built', action='store_true', help='also require and scan all production builds')
    args = parser.parse_args()
    failures = scan(args.built)
    if failures:
        print('\n'.join(failures[:100]))
        print('modelOne scan failed: %s findings' % len(failures))
        sys.exit(1)
    print('modelOne surface scan passed' + (' (including production builds)' if args.built else ''))
