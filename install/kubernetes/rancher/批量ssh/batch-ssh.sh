#!/bin/sh
set -eu
modelone_script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
exec python3 "$modelone_script_dir/batch_ssh.py"
