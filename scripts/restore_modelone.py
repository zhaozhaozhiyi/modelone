#!/usr/bin/env python3
"""Verify and restore metadata into an explicitly named EMPTY MySQL database."""
import argparse
import hashlib
from pathlib import Path
import subprocess

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--client-config',type=Path,required=True)
    parser.add_argument('--database',required=True,help='existing empty isolated restore database')
    parser.add_argument('--backup',type=Path,required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.database.replace('_','').isalnum():parser.error('invalid database identifier')
    if not args.client_config.is_file() or args.client_config.stat().st_mode & 0o077:parser.error('client config must have mode 600')
    expected=args.backup.with_suffix(args.backup.suffix+'.sha256').read_text().split()[0]
    digest=hashlib.sha256()
    with args.backup.open('rb') as source:
        for chunk in iter(lambda:source.read(1024*1024),b''):digest.update(chunk)
    if digest.hexdigest()!=expected:parser.error('backup checksum does not match')
    cli=['mysql','--defaults-extra-file='+str(args.client_config.resolve()),'--batch','--skip-column-names',args.database]
    tables=subprocess.check_output(cli+['--execute','SHOW TABLES'],text=True)
    if tables.strip():parser.error('refusing to overwrite a non-empty database')
    if not args.apply:
        print('Checksum valid and database empty. Add --apply to restore the verified backup.')
    else:
        with args.backup.open('rb') as source:subprocess.run(cli,stdin=source,check=True)
        print('Restored into '+args.database+'; validate before production cutover')
