#!/usr/bin/env bash
set -euo pipefail

target=${1:-.}
base_ref=${2:-HEAD}
repo_root=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || {
  echo "ERROR: $target is not inside a Git repository" >&2
  exit 1
}

git -C "$repo_root" rev-parse --verify "$base_ref^{commit}" >/dev/null 2>&1 || {
  echo "ERROR: base ref does not resolve to a commit: $base_ref" >&2
  exit 1
}

echo "base_ref=$base_ref"
echo "changed_files:"
git -C "$repo_root" diff --name-status "$base_ref" --
git -C "$repo_root" ls-files --others --exclude-standard | sed 's/^/?\t/'

danger=0
while IFS=$'\t' read -r status path rest; do
  [[ -n "${path:-}" ]] || continue
  case "$status" in
    D*|R*)
      printf 'PRUNING_REVIEW: %s %s %s\n' "$status" "$path" "${rest:-}"
      danger=1
      ;;
  esac
  case "$path" in
    */application.yaml|*.application.yaml|*.application.yml|*/components.application-set.yml|*/kustomization.yml|*/kustomization.yaml|*/cluster.yaml)
      printf 'CONTROL_FILE_REVIEW: %s %s\n' "$status" "$path"
      ;;
  esac
done < <(git -C "$repo_root" diff --name-status "$base_ref" --)

if [[ $danger -eq 1 ]]; then
  echo "destructive_review=required"
else
  echo "destructive_review=no_tracked_deletion_detected"
fi

echo "NOTE: inspect list-element removals and untracked-file omissions manually; Git status alone cannot infer rendered pruning."
