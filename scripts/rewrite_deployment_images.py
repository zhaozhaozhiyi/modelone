#!/usr/bin/env python3
"""Rewrite all image fields in deployment manifests from a verified image plan."""
import argparse
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('modelone_image_bundle', ROOT / 'scripts/image_bundle.py')
image_bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_bundle)


def rewrite(plan, manifests, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
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
        print('Rewrote deployment images: ' + str(destination))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True, help='verified images.json')
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, action='append', required=True,
                        help='deployment YAML; may be repeated')
    args = parser.parse_args()
    try:
        rewrite(args.plan, args.manifest, args.output_dir)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))
