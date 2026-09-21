#!/usr/bin/env python3
"""Configure the modelOne repository and keep the source repository read-only.

The command is deliberately explicit: it never invents an enterprise URL,
overwrites an existing ``origin``, or pushes anything.  Run it after the
enterprise Git repository has been provisioned.
"""
import argparse
from pathlib import Path
import subprocess
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UPSTREAM = 'https://github.com/data-infra/cube-studio.git'


def git(repo, *args, check=True):
    return subprocess.run(
        ['git', '-C', str(repo), *args],
        check=check,
        capture_output=True,
        text=True,
    )


def validate_remote(value, label):
    value = value.strip()
    if not value or any(char.isspace() for char in value):
        raise ValueError('%s must be a non-empty Git URL without whitespace' % label)
    # Reject credentials in HTTP(S) remotes. SSH-style URLs are accepted for
    # enterprise Git servers and are validated by Git itself.
    parsed = urlsplit(value)
    if parsed.scheme in ('http', 'https') and (parsed.username or parsed.password):
        raise ValueError('%s must not contain embedded credentials' % label)
    return value


def remote_url(repo, name, push=False):
    args = ['remote', 'get-url']
    if push:
        args.append('--push')
    args.append(name)
    result = git(repo, *args, check=False)
    return result.stdout.strip() if result.returncode == 0 else ''


def configure(repo, origin, upstream=None, apply=False, replace_origin=False):
    repo = Path(repo).resolve()
    if not (repo / '.git').exists():
        raise ValueError('not a Git working tree: %s' % repo)
    origin = validate_remote(origin, 'origin')
    upstream = validate_remote(upstream or DEFAULT_UPSTREAM, 'upstream')

    current_origin = remote_url(repo, 'origin')
    if current_origin and current_origin != origin and not replace_origin:
        raise ValueError(
            'origin already points to %s; pass --replace-origin to change it' % current_origin
        )
    current_upstream = remote_url(repo, 'upstream')
    actions = []
    if not current_origin:
        actions.append(('add', 'origin', origin))
    elif current_origin != origin:
        actions.append(('set-url', 'origin', origin))
    if not current_upstream:
        actions.append(('add', 'upstream', upstream))
    elif current_upstream != upstream:
        actions.append(('set-url', 'upstream', upstream))
    if remote_url(repo, 'upstream', push= True) != 'DISABLED':
        actions.append(('set-push-url', 'upstream', 'DISABLED'))

    if apply:
        for action, name, value in actions:
            if action == 'add':
                git(repo, 'remote', 'add', name, value)
            elif action == 'set-url':
                git(repo, 'remote', 'set-url', name, value)
            else:
                git(repo, 'remote', 'set-url', '--push', name, value)
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origin', required=True, help='enterprise modelOne Git URL')
    parser.add_argument('--upstream', default=DEFAULT_UPSTREAM, help='read-only source repository URL')
    parser.add_argument('--repo', type=Path, default=ROOT, help='working tree to configure')
    parser.add_argument('--replace-origin', action='store_true', help='replace a different existing origin')
    parser.add_argument('--apply', action='store_true', help='write the remote configuration; default is a dry run')
    args = parser.parse_args()
    try:
        actions = configure(args.repo, args.origin, args.upstream, args.apply, args.replace_origin)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
    mode = 'Applied' if args.apply else 'Planned'
    print('%s %s remote change(s) in %s' % (mode, len(actions), Path(args.repo).resolve()))
    for action, name, value in actions:
        # URLs are configuration identifiers; never print embedded credentials.
        print('  %s %s -> %s' % (action, name, value))
    if not args.apply:
        print('Re-run with --apply after reviewing the plan.')


if __name__ == '__main__':
    main()
