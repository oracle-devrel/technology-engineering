#!/usr/bin/env bash
set -euo pipefail

OE_REPOSITORY="https://github.com/oci-landing-zones/oci-landing-zone-operating-entities.git"
OE_RELEASE="v3.1.0"
OE_REVISION="172809932c53467ab20ec6d1b44290a487211b36"
target="${1:-all}"
for command in git jq jsonnet; do
  command -v "$command" >/dev/null || {
    echo "Required command is missing: $command" >&2
    exit 1
  }
done

temporary_directory="$(mktemp -d)"
cleanup() {
  rm -rf "$temporary_directory"
}
trap cleanup EXIT

git -C "$temporary_directory" init --quiet oe
git -C "$temporary_directory/oe" remote add origin "$OE_REPOSITORY"
git -C "$temporary_directory/oe" fetch --quiet --depth 1 origin "$OE_REVISION"
git -C "$temporary_directory/oe" checkout --quiet --detach FETCH_HEAD
test "$(git -C "$temporary_directory/oe" rev-parse HEAD)" = "$OE_REVISION"

environments=()
while IFS= read -r environment; do
  environments+=("$environment")
done < <(
  jsonnet -e '
    std.objectFields((import "config/customer.jsonnet").blueprint.environments)
  ' | jq -r '.[]'
)
test "${#environments[@]}" -gt 0
rendered="$temporary_directory/rendered"
mkdir -p \
  "$rendered/op00_manage_global_landing_zone/generated" \
  "$rendered/op01_manage_landing_zone_environment/generated" \
  "$rendered/op04_manage_project"
for environment in "${environments[@]}"; do
  mkdir -p "$rendered/op02_manage_environment/$environment/generated"
  while IFS= read -r project; do
    mkdir -p \
      "$rendered/op04_manage_project/$environment/$environment-$project/generated"
  done < <(jq -r --arg environment "$environment" \
    '.[$environment][]' config/projects.json)
done
jsonnet -J "$temporary_directory/oe/gen" \
  --multi "$rendered" config/render.jsonnet

if rg -n '__[A-Z0-9_]+__' config/customer.jsonnet; then
  echo "Unresolved customer placeholders remain." >&2
  exit 1
fi
rg -n '__[A-Z0-9_]+__' "$rendered" \
  > "$temporary_directory/rendered-placeholders.txt" || true
if grep -v '__DRG_SPOKES_ROUTE_TABLE_OCID__' \
  "$temporary_directory/rendered-placeholders.txt"; then
  echo "Unexpected generated placeholder remains." >&2
  exit 1
fi

required_files=(
  op00_manage_global_landing_zone/generated/iam.json
  op01_manage_landing_zone_environment/generated/iam.json
  op01_manage_landing_zone_environment/generated/governance.json
  op01_manage_landing_zone_environment/generated/network.json
  op01_manage_landing_zone_environment/generated/observability_cis1.json
  op01_manage_landing_zone_environment/generated/observability_cis1_pre.json
  op01_manage_landing_zone_environment/generated/security_cis1.json
  op01_manage_landing_zone_environment/generated/security_cis1_pre.json
)
for file in "${required_files[@]}"; do
  test -f "$rendered/$file"
done
for file in "$rendered"/op02_manage_environment/*/generated/iam.json; do
  test -f "${file%/iam.json}/network.json"
done
while IFS= read -r file; do
  jq -e 'type == "object"' "$file" >/dev/null
done < <(
  find \
    "$rendered/op00_manage_global_landing_zone/generated" \
    "$rendered/op01_manage_landing_zone_environment/generated" \
    "$rendered/op02_manage_environment" \
    "$rendered/op04_manage_project" \
    -type f -path '*/generated/*.json' | sort
)

case "$target" in
  all)
    roots=(
      op00_manage_global_landing_zone
      op01_manage_landing_zone_environment
    )
    for environment in "${environments[@]}"; do
      roots+=("op02_manage_environment/$environment")
      while IFS= read -r project; do
        roots+=("op04_manage_project/$environment/$environment-$project")
      done < <(jq -r --arg environment "$environment" \
        '.[$environment][]' config/projects.json)
    done
    ;;
  op00)
    roots=(op00_manage_global_landing_zone)
    ;;
  op01)
    roots=(op01_manage_landing_zone_environment)
    ;;
  op02:*)
    environment="${target#op02:}"
    [[ "$environment" =~ ^(dev|test|uat|prod)$ ]]
    roots=("op02_manage_environment/$environment")
    ;;
  op04:*)
    project="${target#op04:}"
    [[ "$project" =~ ^(dev|test|uat|prod)-([a-z][a-z0-9]*(-[a-z0-9]+)*)$ ]]
    environment="${BASH_REMATCH[1]}"
    project_name="${BASH_REMATCH[2]}"
    jq -e --arg environment "$environment" --arg project "$project_name" \
      '.[$environment] | index($project) != null' config/projects.json >/dev/null
    roots=("op04_manage_project/$environment/$project")
    ;;
  *)
    echo "Usage: $0 [all|op00|op01|op02:<environment>|op04:<environment>-<project>]" >&2
    exit 2
    ;;
esac

for root in "${roots[@]}"; do
  source_directory="$rendered/$root/generated"
  target_directory="$root/generated"
  test -d "$source_directory"
  mkdir -p "$target_directory"
  find "$target_directory" -maxdepth 1 -type f -name '*.json' -delete
  cp "$source_directory"/*.json "$target_directory/"
done

echo "Generated $target from $OE_RELEASE ($OE_REVISION)."
