#!/bin/sh
set -eu
export MODELONE_NOTEBOOK_SPARK=true
exec python3 /opt/modelone/notebook_init.py
