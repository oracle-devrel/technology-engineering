#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 <repository-root> <overlay-path> [base-ref]" >&2
  exit 2
fi

repo_root=$(git -C "$1" rev-parse --show-toplevel)
overlay=${2#/}
base_ref=${3:-HEAD}

git -C "$repo_root" rev-parse --verify "$base_ref^{commit}" >/dev/null

temporary=$(mktemp -d "${TMPDIR:-/tmp}/oke-kustomize-diff.XXXXXX")
trap 'rm -rf -- "$temporary"' EXIT
mkdir -p "$temporary/base"
git -C "$repo_root" archive "$base_ref" | tar -x -C "$temporary/base"

if [[ -d "$temporary/base/$overlay" ]]; then
  kubectl kustomize "$temporary/base/$overlay" >"$temporary/before.yml"
else
  : >"$temporary/before.yml"
  echo "base_render=absent"
fi
if [[ -d "$repo_root/$overlay" ]]; then
  kubectl kustomize "$repo_root/$overlay" >"$temporary/after.yml"
else
  : >"$temporary/after.yml"
  echo "worktree_render=absent"
fi
if [[ ! -s "$temporary/before.yml" && ! -s "$temporary/after.yml" ]]; then
  echo "ERROR: overlay is absent from both base and worktree: $overlay" >&2
  exit 1
fi

echo "render_diff=$overlay"
diff -u "$temporary/before.yml" "$temporary/after.yml" || status=$?
status=${status:-0}
if [[ $status -gt 1 ]]; then
  exit "$status"
fi
if [[ $status -eq 0 ]]; then
  echo "render_change=none"
else
  echo "render_change=present"
fi
