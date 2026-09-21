#!/usr/bin/env python3
"""Generate Rancher image transfer scripts without pulling or pushing images."""
import argparse
import importlib.util
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
brand_spec = importlib.util.spec_from_file_location('modelone_brand_config', ROOT / 'myapp/brand.py')
brand_module = importlib.util.module_from_spec(brand_spec)
brand_spec.loader.exec_module(brand_module)
sys.path.insert(0, str(ROOT / 'scripts'))
from image_bundle import generate

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path.cwd())
    args = parser.parse_args()
    images = [line.strip() for line in Path(__file__).with_name('rancher-images-mini.txt').read_text().splitlines() if line.strip()]
    names = {'pull_rancher_images.sh': 'pull-sources', 'push_rancher_harbor.sh': 'copy-images',
             'pull_rancher_harbor.sh': 'pull-targets', 'rancher_image_save.sh': 'save',
             'rancher_image_load.sh': 'load'}
    try:
        registry = os.environ.get('MODELONE_IMAGE_REGISTRY') or brand_module.BRAND['image_registry']
        generate(images, registry, args.output, names)
    except ValueError as error:
        parser.error(str(error))
