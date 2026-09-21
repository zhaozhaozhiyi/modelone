#!/usr/bin/env python3
"""Rewrite all image fields in deployment manifests from a verified image plan."""
import argparse
import json
from pathlib import Path
import importlib.util
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modelone_image_bundle', ROOT / 'scripts/image_bundle.py')
image_bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_bundle)


def stale_image_references(path, references):
    """Find old image values in image fields and controller arguments only."""
    found = set()
    for document in yaml.safe_load_all(path.read_text()):
        def visit(value, key=None):
            if isinstance(value, dict):
                for child_key, child in value.items():
                    visit(child, child_key)
            elif isinstance(value, list):
                for child in value:
                    visit(child, key)
            elif isinstance(value, str):
                if key == 'image':
                    found.update(reference for reference in references if value == reference)
                elif key in ('args', 'command'):
                    found.update(reference for reference in references
                                 if re.search(r'(?<![A-Za-z0-9_./:-])' + re.escape(reference)
                                              + r'(?![A-Za-z0-9_./:-])', value))
        visit(document)
    return sorted(found)


def rewrite(plan, manifests, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_data = json.loads(plan.read_text())
    targets = {row['target'] for row in plan_data.get('images', [])}
    source_references = set()
    for row in plan_data.get('images', []):
        source_references.update([row['runtime'], row['source'], *row.get('runtimeAliases', [])])
    source_references.difference_update(targets)
    names = set()
    for source in manifests:
        source = source.resolve()
        if not source.is_file():
            raise ValueError('Manifest does not exist: ' + str(source))
        name = source.name
        if name in names:
            raise ValueError('Manifest filenames must be unique: ' + name)
        names.add(name)
        destination = output_dir / name
        image_bundle.rewrite_manifest(plan, source, destination)
        stale = stale_image_references(destination, source_references)
        if stale:
            destination.unlink(missing_ok=True)
            raise ValueError('Unrewritten image references remain in ' + name + ': ' + ', '.join(stale[:5]))
        print('Rewrote deployment images: ' + str(destination))


def rewrite_tree(plan, source_root, output_dir):
    """Rewrite every YAML in a source tree while preserving its relative paths."""
    source_root = source_root.resolve()
    if not source_root.is_dir():
        raise ValueError('Manifest source root does not exist: ' + str(source_root))
    manifests = sorted(set(source_root.rglob('*.yaml')) | set(source_root.rglob('*.yml')))
    if not manifests:
        raise ValueError('Manifest source root contains no YAML files: ' + str(source_root))
    output_dir.mkdir(parents=True, exist_ok=True)
    plan_data = json.loads(plan.read_text())
    targets = {row['target'] for row in plan_data.get('images', [])}
    source_references = set()
    for row in plan_data.get('images', []):
        source_references.update([row['runtime'], row['source'], *row.get('runtimeAliases', [])])
    source_references.difference_update(targets)
    for source in manifests:
        destination = output_dir / source.relative_to(source_root)
        image_bundle.rewrite_manifest(plan, source, destination)
        stale = stale_image_references(destination, source_references)
        if stale:
            destination.unlink(missing_ok=True)
            raise ValueError('Unrewritten image references remain in ' + str(source) + ': ' + ', '.join(stale[:5]))
    print('Rewrote deployment manifest tree: ' + str(output_dir))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True, help='verified images.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, action='append', default=[],
                        help='deployment YAML; may be repeated')
    parser.add_argument('--source-root', type=Path,
                        help='rewrite every YAML below this root, preserving relative paths')
    args = parser.parse_args()
    try:
        if bool(args.source_root) == bool(args.manifest):
            parser.error('provide exactly one of --manifest or --source-root')
        if args.source_root:
            rewrite_tree(args.plan, args.source_root, args.output_dir)
        else:
            rewrite(args.plan, args.manifest, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
