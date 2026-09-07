#!/bin/bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$(mktemp -d)"
trap 'rm -rf "$TEST_ROOT"' EXIT

mkdir -p \
  "$TEST_ROOT/source/gitops/argocd" \
  "$TEST_ROOT/source/platform/applications/reference-app" \
  "$TEST_ROOT/source/platform/applications/admin-tool"
printf '%s\n' 'developer placement' > "$TEST_ROOT/source/gitops/argocd/apps.yml"
printf '%s\n' 'reference workload' > "$TEST_ROOT/source/platform/applications/reference-app/app.yml"
printf '%s\n' 'namespaced admin resource' > "$TEST_ROOT/source/platform/applications/admin-tool/resource.yml"

git init --bare "$TEST_ROOT/seed.git" >/dev/null
(
  cd "$TEST_ROOT"
  REPO_CLONE_URL="$TEST_ROOT/seed.git" \
    SOURCE_REPO=source \
    GIT_USERNAME=test \
    GIT_PASSWORD=test \
    SEED_EXCLUDE_PATHS=$'gitops/argocd/apps.yml\nplatform/applications/reference-app' \
    "$PROJECT_ROOT/script/push_repo.sh" >/dev/null
)

seeded_files="$(git --git-dir="$TEST_ROOT/seed.git" ls-tree -r --name-only main)"
grep -qx 'platform/applications/admin-tool/resource.yml' <<<"$seeded_files"
if grep -Eq 'gitops/argocd/apps.yml|platform/applications/reference-app' <<<"$seeded_files"; then
  echo "cluster_admin seed retained a developer placement" >&2
  exit 1
fi

printf '%s\n' 'changed template' > "$TEST_ROOT/source/platform/applications/admin-tool/resource.yml"
(
  cd "$TEST_ROOT"
  REPO_CLONE_URL="$TEST_ROOT/seed.git" \
    SOURCE_REPO=source \
    GIT_USERNAME=test \
    GIT_PASSWORD=test \
    "$PROJECT_ROOT/script/push_repo.sh" >/dev/null
)

preserved_content="$(git --git-dir="$TEST_ROOT/seed.git" show main:platform/applications/admin-tool/resource.yml)"
test "$preserved_content" = 'namespaced admin resource'

git init --bare "$TEST_ROOT/full.git" >/dev/null
(
  cd "$TEST_ROOT"
  REPO_CLONE_URL="$TEST_ROOT/full.git" \
    SOURCE_REPO=source \
    GIT_USERNAME=test \
    GIT_PASSWORD=test \
    "$PROJECT_ROOT/script/push_repo.sh" >/dev/null
)
full_files="$(git --git-dir="$TEST_ROOT/full.git" ls-tree -r --name-only main)"
grep -qx 'gitops/argocd/apps.yml' <<<"$full_files"
grep -qx 'platform/applications/reference-app/app.yml' <<<"$full_files"

echo "Repository scope seeding and customer-content preservation succeeded"
