#!/usr/bin/env python3
"""Fetch the pinned Label Studio source without overwriting local development."""
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def fetch():
    lock = json.loads((ROOT / 'integrations/label-studio/upstream.json').read_text())
    target = ROOT / lock['source_directory']
    if target.exists():
        if not (target / '.git').exists():
            raise ValueError('Source directory already exists and is not a Git checkout')
        origin = subprocess.check_output(['git', '-C', str(target), 'remote', 'get-url', 'origin'], text=True).strip()
        commit = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        if origin != lock['repository'] or commit != lock['commit']:
            raise ValueError('Existing checkout differs from the pinned source; local work was preserved')
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(['git', 'clone', '--depth', '1', '--branch', lock['tag'], lock['repository'], str(target)], check=True)
        commit = subprocess.check_output(['git', '-C', str(target), 'rev-parse', 'HEAD'], text=True).strip()
        if commit != lock['commit']:
            raise ValueError('Upstream tag does not match the pinned commit; do not build this checkout')
        subprocess.run(['git', '-C', str(target), 'switch', '-c', 'codex/modelone-integration'], check=True)
    return target


if __name__ == '__main__':
    print('Pinned Label Studio source: ' + str(fetch()))
