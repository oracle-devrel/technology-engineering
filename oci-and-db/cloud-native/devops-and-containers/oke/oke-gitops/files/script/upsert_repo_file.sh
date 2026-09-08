#!/bin/bash

set -euo pipefail

CLONED_DIR="$(basename "$REPO_CLONE_URL" .git)"
SOURCE_FILE="${SOURCE_FILE#/}"
SOURCE_PATH="${PWD}/${SOURCE_FILE}"
CREDENTIAL_HELPER='!f() { printf "username=%s\npassword=%s\n" "$GIT_USERNAME" "$GIT_PASSWORD"; }; f'
OVERWRITE_REPOSITORY="${OVERWRITE_REPOSITORY:-false}"

test -n "$CLONED_DIR"
test -f "$SOURCE_PATH"
test -n "$TARGET_FILE"

case "$OVERWRITE_REPOSITORY" in
  true | false) ;;
  *)
    echo "OVERWRITE_REPOSITORY must be true or false" >&2
    exit 2
    ;;
esac

case "$TARGET_FILE" in
  /* | ../* | */../* | *"/.." | . | ..)
    echo "TARGET_FILE must be a repository-relative file path" >&2
    exit 2
    ;;
esac

rm -rf -- "./${CLONED_DIR}"
trap 'rm -rf -- "./${CLONED_DIR}"' EXIT

git -c credential.helper="$CREDENTIAL_HELPER" \
  clone "$REPO_CLONE_URL" "$CLONED_DIR"

if git -C "$CLONED_DIR" rev-parse --verify HEAD >/dev/null 2>&1 &&
  test "$OVERWRITE_REPOSITORY" = false; then
  echo "Repository already has customer-owned content; preserving it unchanged"
  exit 0
fi

mkdir -p "${CLONED_DIR}/$(dirname "$TARGET_FILE")"
cp "$SOURCE_PATH" "${CLONED_DIR}/${TARGET_FILE}"

cd "$CLONED_DIR"
git config user.email "resource-manager@oracle.com"
git config user.name "$GIT_USERNAME"
git add -- "$TARGET_FILE"

if git diff --cached --quiet; then
  echo "$TARGET_FILE already matches the generated adapter"
  exit 0
fi

git commit -m "Connect optional fleet-config repository"
git -c credential.helper="$CREDENTIAL_HELPER" push origin HEAD:main
