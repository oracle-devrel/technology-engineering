#!/bin/bash
set -euo pipefail

require_env() {
  local name="$1"
  if [ -z "${!name:-}" ]; then
    echo "Missing required environment variable: ${name}" >&2
    exit 1
  fi
}

require_env REGION
require_env GIT_USERNAME
require_env GIT_PASSWORD
require_env REPO_CLONE_URL
require_env SOURCE_REPO
require_env SEED_MODE
require_env SEED_PATHS

if [[ ! "$REGION" =~ ^[a-z]{2}(-[a-z]+)*-[a-z]+-[0-9]+$ ]]; then
  echo "Invalid OCI region: ${REGION}" >&2
  exit 1
fi

if [[ "$REPO_CLONE_URL" != https://devops.scmservice."${REGION}".oci.oraclecloud.com/* ]]; then
  echo "Repository URL must be an OCI DevOps HTTPS URL for ${REGION}" >&2
  exit 1
fi

if [ "$SEED_MODE" != "empty-repository" ] && [ "$SEED_MODE" != "add-only" ] && [ "$SEED_MODE" != "refresh" ]; then
  echo "SEED_MODE must be empty-repository, add-only, or refresh." >&2
  exit 1
fi

if [[ "$SOURCE_REPO" = /* ]]; then
  SOURCE_REPO=".${SOURCE_REPO}"
fi

if [[ "$SOURCE_REPO" = *".."* ]] || [ ! -d "$SOURCE_REPO" ]; then
  echo "Invalid source repository path: ${SOURCE_REPO}" >&2
  exit 1
fi

WORK_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$WORK_DIR"
}
trap cleanup EXIT

mkdir -p "${WORK_DIR}/home"
export HOME="${WORK_DIR}/home"

cat >>"${HOME}/.netrc" <<EOF
machine devops.scmservice.${REGION}.oci.oraclecloud.com
       login ${GIT_USERNAME}
       password ${GIT_PASSWORD}
EOF
chmod 600 "${HOME}/.netrc"

git clone "${REPO_CLONE_URL}" "${WORK_DIR}/repo"

if [ "$SEED_MODE" = "empty-repository" ] && git -C "${WORK_DIR}/repo" rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "Repository already contains a commit; preserving developer-owned content."
  exit 0
fi

added_paths=0
if [ -n "${REMOVE_PATHS:-}" ]; then
  if [ "$SEED_MODE" != "refresh" ]; then
    echo "REMOVE_PATHS is allowed only in refresh mode." >&2
    exit 1
  fi
  while IFS= read -r relative_path || [ -n "$relative_path" ]; do
    [ -n "$relative_path" ] || continue
    if [[ "$relative_path" = /* ]] || [[ "$relative_path" = *".."* ]]; then
      echo "Invalid removal path: ${relative_path}" >&2
      exit 1
    fi
    destination_path="${WORK_DIR}/repo/${relative_path}"
    if [ -e "$destination_path" ]; then
      rm -rf "$destination_path"
      echo "Removed obsolete template path: ${relative_path}"
      added_paths=$((added_paths + 1))
    fi
  done <<<"$REMOVE_PATHS"
fi

while IFS= read -r relative_path || [ -n "$relative_path" ]; do
  [ -n "$relative_path" ] || continue

  if [[ "$relative_path" = /* ]] || [[ "$relative_path" = *".."* ]]; then
    echo "Invalid seed path: ${relative_path}" >&2
    exit 1
  fi

  source_path="${SOURCE_REPO}/${relative_path}"
  destination_path="${WORK_DIR}/repo/${relative_path}"

  if [ ! -e "$source_path" ]; then
    echo "Seed source does not exist: ${source_path}" >&2
    exit 1
  fi

  if [ -e "$destination_path" ] && [ "$SEED_MODE" != "refresh" ]; then
    echo "Preserving existing path: ${relative_path}"
    continue
  fi

  mkdir -p "$(dirname "$destination_path")"
  if [ "$SEED_MODE" = "refresh" ] && [ -d "$source_path" ]; then
    mkdir -p "$destination_path"
    cp -a "$source_path/." "$destination_path/"
    echo "Refreshed template path: ${relative_path}"
  else
    cp -a "$source_path" "$destination_path"
    echo "$([ "$SEED_MODE" = "refresh" ] && echo Refreshed || echo Added) template path: ${relative_path}"
  fi
  added_paths=$((added_paths + 1))
done <<<"$SEED_PATHS"

if [ "$added_paths" -eq 0 ]; then
  echo "No starter paths were added."
  exit 0
fi

cd "${WORK_DIR}/repo"
git config user.email "resource-manager@oracle.com"
git config user.name "${GIT_USERNAME}"

git add .

if git diff --cached --quiet; then
  echo "No repository content changes to push."
  exit 0
fi

git commit -m "$([ "$SEED_MODE" = "refresh" ] && echo Refresh || echo Add) Resource Manager template files"
git push origin HEAD:main
