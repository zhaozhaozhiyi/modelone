#!/usr/bin/env python3
"""Preview owned resource replacements in exported data; --apply writes backups.

Does not operate on a source tree, licenses, identifiers or arbitrary binaries.
Database upgrades use the Alembic migration instead.
"""
import argparse
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'myapp' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def migrate(root, apply=False):
    brand = load('brand')
    migration = load('brand_migration')
    if (root / '.git').exists():
        raise ValueError('Use an isolated export directory, not a Git source tree')
    count = 0
    for path in sorted(root.rglob('*')):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.json', '.csv', '.yaml', '.yml'):
            continue
        old = path.read_text(encoding='utf-8')
        new = migration.rewrite(old, brand.resolve_resources, brand.BRAND['help_url'])
        if old != new:
            print(path.relative_to(root))
            if apply:
                backup = path.with_suffix(path.suffix + '.bak')
                with backup.open('x', encoding='utf-8') as f:
                    f.write(old)
                path.write_text(new, encoding='utf-8')
            count += 1
    return count

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('root must be an existing export directory')
    print('%s %s files' % ('Updated' if args.apply else 'Would update', migrate(args.root.resolve(), args.apply)))
