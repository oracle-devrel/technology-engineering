#!/usr/bin/env bash
set -euo pipefail

target=${1:-.}
repo_root=$(git -C "$target" rev-parse --show-toplevel 2>/dev/null) || {
  echo "ERROR: $target is not inside a Git repository" >&2
  exit 1
}

command -v kubectl >/dev/null 2>&1 || {
  echo "ERROR: kubectl is required for Kustomize rendering" >&2
  exit 1
}

validated_kustomize=0
while IFS= read -r kustomization; do
  directory=${kustomization%/*}
  printf 'kustomize: %s\n' "${directory#"$repo_root"/}"
  kubectl kustomize "$directory" >/dev/null
  validated_kustomize=$((validated_kustomize + 1))
done < <(find "$repo_root" -type f \( -name kustomization.yml -o -name kustomization.yaml \) -print | LC_ALL=C sort)

validated_helm=0
if command -v helm >/dev/null 2>&1; then
  while IFS= read -r chart_file; do
    chart_dir=${chart_file%/*}
    case "$chart_dir" in
      */charts/*) continue ;;
    esac
    printf 'helm lint: %s\n' "${chart_dir#"$repo_root"/}"
    helm lint "$chart_dir" >/dev/null
    validated_helm=$((validated_helm + 1))
  done < <(find "$repo_root" -type f -name Chart.yaml -print | LC_ALL=C sort)

  while IFS= read -r selected_values; do
    chart_dir=${selected_values%%/values/*}
    [[ -f "$chart_dir/Chart.yaml" && -f "$chart_dir/values.yaml" ]] || continue
    relative=${selected_values#"$chart_dir"/values/}
    environment=${relative%%/*}
    component=${relative##*/}
    component=${component%.yml}
    component=${component%.yaml}
    release=$(printf '%s-%s-%s' "$(basename "$(dirname "$chart_dir")")" "$component" "$environment" | tr '_' '-')
    printf 'helm selection: %s + %s\n' "${chart_dir#"$repo_root"/}/values.yaml" "${selected_values#"$repo_root"/}"
    helm lint "$chart_dir" -f "$chart_dir/values.yaml" -f "$selected_values" >/dev/null
    helm template "$release" "$chart_dir" -f "$chart_dir/values.yaml" -f "$selected_values" >/dev/null
    validated_helm=$((validated_helm + 1))
  done < <(find "$repo_root" -type f \( -path '*/values/dev/*.yml' -o -path '*/values/dev/*.yaml' -o -path '*/values/staging/*.yml' -o -path '*/values/staging/*.yaml' -o -path '*/values/production/*.yml' -o -path '*/values/production/*.yaml' \) -print | LC_ALL=C sort)
else
  if find "$repo_root" -type f -name Chart.yaml -print -quit | grep -q .; then
    echo "ERROR: helm is required because this repository contains charts" >&2
    exit 1
  fi
fi

printf 'validated_kustomize_roots=%s\n' "$validated_kustomize"
printf 'validated_helm_operations=%s\n' "$validated_helm"
echo "validation=passed"
