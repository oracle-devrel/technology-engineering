#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 4 || $# -gt 5 ]]; then
  echo "usage: $0 <repository-root> <application> <component> <environment> [base-ref]" >&2
  exit 2
fi

repo_root=$(git -C "$1" rev-parse --show-toplevel)
application=$2
component=$3
environment=$4
base_ref=${5:-HEAD}
chart_path="applications/$application/helm"
selected_path="$chart_path/values/$environment/$component.yml"

git -C "$repo_root" rev-parse --verify "$base_ref^{commit}" >/dev/null

temporary=$(mktemp -d "${TMPDIR:-/tmp}/oke-helm-diff.XXXXXX")
trap 'rm -rf -- "$temporary"' EXIT
mkdir -p "$temporary/base"
git -C "$repo_root" archive "$base_ref" | tar -x -C "$temporary/base"

release="$application-$component-$environment"
if [[ -f "$temporary/base/$chart_path/Chart.yaml" && -f "$temporary/base/$chart_path/values.yaml" && -f "$temporary/base/$selected_path" ]]; then
  helm template "$release" "$temporary/base/$chart_path" \
    --namespace "$application" \
    -f "$temporary/base/$chart_path/values.yaml" \
    -f "$temporary/base/$selected_path" >"$temporary/before.yml"
else
  : >"$temporary/before.yml"
  echo "base_render=absent"
fi
if [[ -f "$repo_root/$chart_path/Chart.yaml" && -f "$repo_root/$chart_path/values.yaml" && -f "$repo_root/$selected_path" ]]; then
  helm template "$release" "$repo_root/$chart_path" \
    --namespace "$application" \
    -f "$repo_root/$chart_path/values.yaml" \
    -f "$repo_root/$selected_path" >"$temporary/after.yml"
else
  : >"$temporary/after.yml"
  echo "worktree_render=absent"
fi
if [[ ! -s "$temporary/before.yml" && ! -s "$temporary/after.yml" ]]; then
  echo "ERROR: selection is absent from both base and worktree: $application/$component/$environment" >&2
  exit 1
fi

echo "render_diff=$application/$component/$environment"
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
