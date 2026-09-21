"""Notebook launch helpers, independent of application startup."""
import re
import shlex


def parse_environment(value):
    result = {}
    for line in (value or '').splitlines():
        if '=' not in line:
            continue
        key, content = line.strip().split('=', 1)
        key = key.strip()
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ValueError('Invalid notebook environment variable name')
        result[key] = content
    return result


def initialization_command(username):
    user_init = shlex.quote('/mnt/' + username + '/init.sh')
    # Platform setup completes before the IDE starts. User startup hooks remain
    # asynchronous for compatibility with long-running environment installers.
    return ('if [ -f /init.sh ]; then sh /init.sh > /notebook_init.log 2>&1 || '
            '{ cat /notebook_init.log >&2; exit 1; }; fi; '
            'if [ -f ' + user_init + ' ]; then nohup sh ' + user_init +
            ' > /init.log 2>&1 & fi; ')
