#!/bin/bash

# This file is sourced by the cluster entrypoints. It maps every source
# manifest reference to the image-rewritten release tree before kubectl runs.
if [ "${MODELONE_MANIFEST_HELPER_LOADED:-}" = "1" ]; then
  return 0
fi
MODELONE_MANIFEST_HELPER_LOADED=1

MODELONE_SOURCE_ROOT="${MODELONE_SOURCE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
MODELONE_RELEASE_DIR="${MODELONE_RELEASE_DIR:-$MODELONE_SOURCE_ROOT/../../dist/modelone}"
MODELONE_KUBERNETES_MANIFEST="${MODELONE_KUBERNETES_MANIFEST:-$MODELONE_RELEASE_DIR/kubernetes.yaml}"
MODELONE_MANIFEST_ROOT="${MODELONE_MANIFEST_ROOT:-$MODELONE_RELEASE_DIR/platform-manifests/kubernetes}"
MODELONE_ARGO_MANIFEST_DIR="${MODELONE_ARGO_MANIFEST_DIR:-$MODELONE_MANIFEST_ROOT/argo}"

for manifest in "$MODELONE_KUBERNETES_MANIFEST" \
  "$MODELONE_ARGO_MANIFEST_DIR/install-3.4.3-all.yaml" \
  "$MODELONE_MANIFEST_ROOT/kubeflow/train-operator/manifests/overlays/standalone/kustomization.yaml"; do
  if [ ! -f "$manifest" ]; then
    echo "错误：缺少 modelOne 发布清单 $manifest，请先生成并校验企业镜像清单"
    return 1
  fi
done

modelone_source_relative() {
  local path="$1"
  path="${path#./}"
  local current="${PWD#"$MODELONE_SOURCE_ROOT"}"
  current="${current#/}"
  if [ -n "$current" ]; then
    path="$current/$path"
  fi
  case "$path" in
    /*|../*|*/../*|*/*/../*)
      echo "错误：非法 modelOne 清单路径 $1" >&2
      return 1
      ;;
  esac
  printf '%s/%s' "$MODELONE_MANIFEST_ROOT" "$path"
}

modelone_manifest() {
  local source="$1"
  if [ "$source" = "$MODELONE_KUBERNETES_MANIFEST" ] ||
     [[ "$source" == "$MODELONE_ARGO_MANIFEST_DIR/"* ]]; then
    printf '%s' "$source"
    return 0
  fi
  local target
  target="$(modelone_source_relative "$source")" || return 1
  if [ ! -f "$target" ]; then
    echo "错误：发布清单中缺少 $source 对应的 $target" >&2
    return 1
  fi
  printf '%s' "$target"
}

modelone_kustomize() {
  local source="$1"
  local target
  target="$(modelone_source_relative "$source")" || return 1
  if [ ! -f "$target/kustomization.yaml" ] && [ ! -f "$target/kustomization.yml" ]; then
    echo "错误：发布清单中缺少 Kustomize 目录 $target" >&2
    return 1
  fi
  printf '%s' "$target"
}

kubectl() {
  local rewritten=()
  while [ "$#" -gt 0 ]; do
    case "$1" in
      -f|--filename)
        rewritten+=("$1")
        shift
        if [ "$#" -eq 0 ]; then
          echo "错误：kubectl 缺少清单路径" >&2
          return 2
        fi
        local mapped_manifest
        mapped_manifest="$(modelone_manifest "$1")" || return 1
        rewritten+=("$mapped_manifest")
        ;;
      -k|--kustomize)
        rewritten+=("$1")
        shift
        if [ "$#" -eq 0 ]; then
          echo "错误：kubectl 缺少 Kustomize 路径" >&2
          return 2
        fi
        local mapped_kustomize
        mapped_kustomize="$(modelone_kustomize "$1")" || return 1
        rewritten+=("$mapped_kustomize")
        ;;
      *)
        rewritten+=("$1")
        ;;
    esac
    shift
  done
  command kubectl "${rewritten[@]}"
}
