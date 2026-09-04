#!/bin/bash

set -euo pipefail

CLONED_DIR="$(basename "$REPO_CLONE_URL" .git)"
SOURCE_REPO="${SOURCE_REPO#/}"
SOURCE_PATH="${PWD}/${SOURCE_REPO}"
CREDENTIAL_HELPER='!f() { printf "username=%s\npassword=%s\n" "$GIT_USERNAME" "$GIT_PASSWORD"; }; f'
OVERWRITE_REPOSITORY="${OVERWRITE_REPOSITORY:-false}"

test -n "$CLONED_DIR"
test -d "$SOURCE_PATH"
test "$SOURCE_PATH" != "${PWD}/${CLONED_DIR}"

case "$OVERWRITE_REPOSITORY" in
  true | false) ;;
  *)
    echo "OVERWRITE_REPOSITORY must be true or false" >&2
    exit 2
    ;;
esac

rm -rf -- "./${CLONED_DIR}"
trap 'rm -rf -- "./${CLONED_DIR}"' EXIT

git -c credential.helper="$CREDENTIAL_HELPER" \
  clone "$REPO_CLONE_URL" "$CLONED_DIR"

if git -C "$CLONED_DIR" rev-parse --verify HEAD >/dev/null 2>&1 &&
  test "$OVERWRITE_REPOSITORY" = false; then
  # OCI DevOps initializes a new hosted repository with an empty commit. That
  # commit is provider-owned bootstrap state, not customer content, so it must
  # not prevent the initial template from being seeded.
  if test -n "$(git -C "$CLONED_DIR" ls-tree -r --name-only HEAD)"; then
    echo "Repository already has customer-owned content; preserving it unchanged"
    exit 0
  fi

  echo "Repository contains only the OCI DevOps empty initial commit; seeding it"
fi

find "$CLONED_DIR" -mindepth 1 -maxdepth 1 ! -name .git \
  -exec rm -rf -- {} +
cp -a "${SOURCE_PATH}/." "${CLONED_DIR}/"

cd "$CLONED_DIR"
git config user.email "resource-manager@oracle.com"
git config user.name "$GIT_USERNAME"

# Git records the executable bit from the filesystem when files are added.
find . -type f -name "*.sh" -exec chmod +x {} \;
git add --all

if git diff --cached --quiet; then
  echo "Repository already matches the requested seed content"
  exit 0
fi

git commit -m "Seed repository from Resource Manager"
git -c credential.helper="$CREDENTIAL_HELPER" push origin HEAD:main
