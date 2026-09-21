#!/usr/bin/env python3
"""Generate and execute traceable Docker image transfer plans. No shell evaluation."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

IMAGE = re.compile(r'(?:[a-z0-9][a-z0-9._-]*(?::[0-9]+)?/)*[a-z0-9][a-z0-9._-]*(?::[A-Za-z0-9_][A-Za-z0-9_.-]{0,127})?')


def check_image(value):
    if not isinstance(value, str) or not IMAGE.fullmatch(value):
        raise ValueError('Invalid image reference in transfer plan')
    return value


def file_digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def write_plan(path, plan):
    temporary = path.with_suffix('.json.part')
    temporary.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(path)


def generate(images, registry, output, filenames=None):
    registry = registry.strip().rstrip('/')
    if not registry:
        raise ValueError('MODELONE_IMAGE_REGISTRY is required, for example registry.example.com/team')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*(?::[0-9]{1,5})?(?:/[a-z0-9]+(?:[._-][a-z0-9]+)*)*', registry):
        raise ValueError('Registry must be a host/path without credentials or shell syntax')
    if registry.endswith('/modelone'):
        raise ValueError('Do not append modelone to MODELONE_IMAGE_REGISTRY')
    prefix = registry + '/modelone/'
    records = []
    for original in sorted(set(images)):
        check_image(original)
        if original.startswith('modelone/') or original.startswith(prefix):
            target = original if original.startswith(prefix) else registry + '/' + original
            # These product images must already be rebuilt in the enterprise
            # registry. There is no assumed public modelone Docker Hub account.
            source = target
        else:
            components = original.split('/')
            if len(components) == 1:
                components = ['docker.io', 'library', original]
            elif not ('.' in components[0] or ':' in components[0] or components[0] == 'localhost'):
                components.insert(0, 'docker.io')
            if len(components) > 1 and components[1] == 'cube-argoproj':
                components[1] = 'argoproj'
            target = prefix + 'third-party/' + '/'.join(components)
            source = original
        check_image(target)
        duplicate = next((row for row in records if row['target'] == target), None)
        if duplicate:
            if duplicate['source'] != source:
                raise ValueError('Multiple sources resolve to the same enterprise target')
            duplicate.setdefault('runtimeAliases', []).append(original)
            continue
        records.append({'runtime': original, 'source': source, 'target': target,
                        'archive': 'archives/' + hashlib.sha256(target.encode()).hexdigest()[:24] + '.tar.gz'})
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / 'images.json'
    if plan_path.exists():
        raise ValueError('Output already contains images.json; use a new output directory to preserve evidence')
    write_plan(plan_path, {'schemaVersion': 1, 'registry': registry, 'images': records})
    license_source = Path(__file__).resolve().parents[1] / 'LICENSE'
    if license_source.is_file():
        licenses = output / 'licenses'
        licenses.mkdir(exist_ok=True)
        shutil.copyfile(license_source, licenses / 'LICENSE')
    helper = output / 'image_bundle.py'
    if helper.resolve() != Path(__file__).resolve():
        shutil.copyfile(__file__, helper)
    names = filenames or {
        'pull_images.sh': 'pull-sources', 'push_harbor.sh': 'copy-images',
        'pull_harbor.sh': 'pull-targets', 'image_save.sh': 'save', 'image_load.sh': 'load',
    }
    for name, action in names.items():
        if Path(name).name != name:
            raise ValueError('Script name must not contain a directory')
        script = output / name
        script.write_text('#!/bin/sh\nset -eu\n'
                          'bundle_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"\n'
                          'exec python3 "$bundle_dir/image_bundle.py" --plan "$bundle_dir/images.json" '
                          + action + '\n')
        script.chmod(0o755)
    (output / 'README.txt').write_text(
        'modelOne image transfer package\n\n'
        'images.json records runtime references, source and enterprise target.\n'
        'Product images must be rebuilt and present at the enterprise target.\n'
        'Authenticate with docker login before copy-images or pull-targets.\n'
        'Run copy-images online, then save to package already cached target images.\n'
        'Copy this entire directory to the offline node and run load.\n'
        'Python 3 and Docker are required. No network is used by save, verify or load.\n'
        'load validates ALL archive checksums before importing the first image.\n'
        'Update workload references to target values; old public aliases are not restored.\n'
        'This Docker package contains the local platform only, recorded after save.\n'
        'For multi-platform registry migration use the separate skopeo workflow.\n'
        'Retain licenses/LICENSE; collect every image SBOM and third-party license\n'
        'before delivery. This generated plan is not full deployment acceptance.\n')
    print(str(len(records)) + ' image references planned: ' + str(plan_path))
    return plan_path


def manifest_images(paths):
    # Only consume rendered manifests. Reject unresolved image expressions so
    # deployment-specific dependencies cannot disappear silently from a plan.
    import yaml
    result = []
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == 'image' and isinstance(item, str):
                    result.append(check_image(item))
                else:
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    for path in paths:
        for document in yaml.safe_load_all(path.read_text()):
            visit(document)
    return result


def image_mapping(plan_path):
    plan = json.loads(plan_path.read_text())
    if plan.get('schemaVersion') != 1:
        raise ValueError('Unsupported image plan')
    mapping = {}
    for row in plan['images']:
        target = check_image(row['target'])
        for source in [row['runtime'], row['source'], target] + row.get('runtimeAliases', []):
            check_image(source)
            if source in mapping and mapping[source] != target:
                raise ValueError('Conflicting image mapping')
            mapping[source] = target
    return mapping


def rewrite_images(value, mapping):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == 'image' and isinstance(item, str):
                if item not in mapping:
                    raise ValueError('Deployment image is missing from the transfer plan: ' + item)
                value[key] = mapping[item]
            elif key in ('args', 'command'):
                value[key] = rewrite_image_tokens(item, mapping)
            else:
                rewrite_images(item, mapping)
    elif isinstance(value, list):
        for item in value:
            rewrite_images(item, mapping)
    return value


def rewrite_image_tokens(value, mapping):
    """Rewrite image references embedded in controller command arguments."""
    if isinstance(value, dict):
        return {key: rewrite_image_tokens(item, mapping) for key, item in value.items()}
    if isinstance(value, list):
        return [rewrite_image_tokens(item, mapping) for item in value]
    if not isinstance(value, str):
        return value
    for source in sorted(mapping, key=len, reverse=True):
        value = value.replace(source, mapping[source])
    return value


def rewrite_manifest(plan_path, source_path, output_path):
    import yaml
    documents = list(yaml.safe_load_all(source_path.read_text()))
    mapping = image_mapping(plan_path)
    rewrite_images(documents, mapping)
    rewrite_kustomization_images(documents, mapping)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump_all(documents, allow_unicode=True, sort_keys=False))


def rewrite_kustomization_images(documents, mapping):
    """Rewrite Kustomize image transformers alongside workload image fields."""
    for document in documents:
        if not isinstance(document, dict) or document.get('kind') != 'Kustomization':
            continue
        for image in document.get('images', []):
            if not isinstance(image, dict) or not isinstance(image.get('name'), str):
                continue
            name = image['name']
            candidate = name
            if image.get('newTag'):
                candidate += ':' + str(image['newTag'])
            target = mapping.get(candidate) or mapping.get(name)
            if not target:
                raise ValueError('Kustomize image is missing from the transfer plan: ' + candidate)
            target_name, separator, target_tag = target.rpartition(':')
            if not separator or '/' in target_tag:
                raise ValueError('Kustomize target must include a tag: ' + target)
            image['newName'] = target_name
            image['newTag'] = target_tag


def inspect(image):
    result = json.loads(subprocess.check_output(['docker', 'image', 'inspect', image], text=True))[0]
    return {'imageId': result['Id'], 'platform': result['Os'] + '/' + result['Architecture']
            + ('/' + result['Variant'] if result.get('Variant') else '')}


def checked_archive(folder, row):
    path = (folder / row['archive']).resolve()
    path.relative_to(folder.resolve())
    if not row.get('sha256') or not row.get('imageId') or file_digest(path) != row['sha256']:
        raise ValueError('Missing or mismatched archive evidence: ' + row['archive'])
    return path


def execute(plan_path, action):
    plan = json.loads(plan_path.read_text())
    if plan.get('schemaVersion') != 1 or not plan.get('images'):
        raise ValueError('Empty or unsupported image plan')
    folder = plan_path.parent
    for row in plan['images']:
        for key in ('source', 'target', 'runtime'):
            check_image(row[key])
        (folder / row['archive']).resolve().relative_to(folder.resolve())
    # Verify the entire package before the first mutation of Docker state.
    if action in ('load', 'verify'):
        for row in plan['images']:
            checked_archive(folder, row)
        if action == 'verify':
            print('All image archive checksums passed')
            return
    for row in plan['images']:
        source, target = row['source'], row['target']
        if action in ('pull-sources', 'copy-images'):
            subprocess.run(['docker', 'pull', source], check=True)
            if action == 'copy-images' and source != target:
                subprocess.run(['docker', 'tag', source, target], check=True)
                subprocess.run(['docker', 'push', target], check=True)
        elif action == 'pull-targets':
            subprocess.run(['docker', 'pull', target], check=True)
        elif action == 'save':
            metadata = inspect(target)  # No network or implicit pull during packaging.
            archive = folder / row['archive']
            archive.parent.mkdir(parents=True, exist_ok=True)
            temporary = archive.with_suffix(archive.suffix + '.part')
            process = subprocess.Popen(['docker', 'save', target], stdout=subprocess.PIPE)
            try:
                with gzip.open(temporary, 'wb') as output:
                    shutil.copyfileobj(process.stdout, output)
                process.stdout.close()
                if process.wait() != 0:
                    raise ValueError('Docker save failed; archive was not accepted')
            except BaseException:
                process.stdout.close()
                if process.poll() is None:
                    process.terminate()
                process.wait()
                raise
            temporary.replace(archive)
            row.update(metadata, sha256=file_digest(archive), bytes=archive.stat().st_size)
            write_plan(plan_path, plan)
        elif action == 'load':
            subprocess.run(['docker', 'load', '--input', str(folder / row['archive'])], check=True)
            if inspect(target)['imageId'] != row['imageId']:
                raise ValueError('Loaded image ID differs from packaging evidence')
        print(action + ': ' + target)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('action', choices=['pull-sources', 'copy-images', 'pull-targets', 'save', 'verify', 'load', 'rewrite'])
    parser.add_argument('--manifest', type=Path, help='rendered YAML to rewrite with enterprise image references')
    parser.add_argument('--output', type=Path, help='rewritten YAML destination')
    args = parser.parse_args()
    try:
        if args.action == 'rewrite':
            if not args.manifest or not args.output:
                parser.error('rewrite requires --manifest and --output')
            rewrite_manifest(args.plan, args.manifest, args.output)
        else:
            execute(args.plan, args.action)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
