#!/usr/bin/env bash
set -euo pipefail

target=${1:-.}

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required" >&2
  exit 1
fi

repo_root=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || {
  echo "ERROR: $target is not inside a Git repository" >&2
  exit 1
}

repo_type=unknown
if [[ -d "$repo_root/platform" && -d "$repo_root/bootstrap" ]]; then
  repo_type=cluster-config
elif [[ -d "$repo_root/clusters" && -d "$repo_root/profiles" ]]; then
  repo_type=fleet-config
elif [[ -d "$repo_root/applications" && ! -d "$repo_root/platform" ]]; then
  repo_type=apps-config
elif [[ -d "$repo_root/script" && -f "$repo_root/mirror_argocd.yaml" ]]; then
  repo_type=pipelines
fi

printf 'repository_root=%s\n' "$repo_root"
printf 'repository_type=%s\n' "$repo_type"
printf 'branch=%s\n' "$(git -C "$repo_root" branch --show-current)"
printf 'head=%s\n' "$(git -C "$repo_root" rev-parse --short HEAD)"

if [[ -n "$(git -C "$repo_root" status --porcelain)" ]]; then
  echo "working_tree=dirty"
  git -C "$repo_root" status --short
else
  echo "working_tree=clean"
fi

for tool in kubectl helm; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s=available\n' "$tool"
  else
    printf '%s=missing\n' "$tool"
  fi
done

if [[ "$repo_type" == unknown ]]; then
  echo "ERROR: repository does not match a supported OKE GitOps repository" >&2
  exit 2
fi
