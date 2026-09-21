#!/usr/bin/env python3
"""Create a MySQL metadata backup and checksum using a protected client config."""
import argparse
import hashlib
from pathlib import Path
import subprocess

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-config', type=Path, required=True)
    parser.add_argument('--database', default='kubeflow')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if not args.client_config.is_file() or args.client_config.stat().st_mode & 0o077:
        parser.error('client config must exist and be readable only by its owner (chmod 600)')
    if not args.database.replace('_','').isalnum():
        parser.error('database must be an identifier')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + '.partial')
    if args.output.exists() or temporary.exists():
        parser.error('output already exists; choose a new backup path')
    try:
        with temporary.open('xb') as output:
            temporary.chmod(0o600)
            subprocess.run(['mysqldump', '--defaults-extra-file='+str(args.client_config.resolve()), '--single-transaction', '--routines', '--triggers', '--events', args.database], stdout=output, check=True)
        digest = hashlib.sha256()
        with temporary.open('rb') as source:
            for chunk in iter(lambda:source.read(1024*1024), b''):
                digest.update(chunk)
        temporary.replace(args.output)
        args.output.with_suffix(args.output.suffix+'.sha256').write_text(digest.hexdigest()+'  '+args.output.name+'\n')
        print('Backup and SHA-256 saved: '+str(args.output))
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
