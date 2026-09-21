#!/bin/sh
set -eu
: "${MODELONE_IMAGE_BUNDLE_DIR:?Set MODELONE_IMAGE_BUNDLE_DIR to a generated offline image package}"
bundle_dir=$(CDPATH= cd -- "$MODELONE_IMAGE_BUNDLE_DIR" && pwd)
exec sh "$bundle_dir/image_load.sh"
