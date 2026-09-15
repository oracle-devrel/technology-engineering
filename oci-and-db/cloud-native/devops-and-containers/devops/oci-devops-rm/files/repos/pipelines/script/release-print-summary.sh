#!/bin/bash
set -euo pipefail

unset -v RELEASE_ENV_FILE
unset -v PROMOTION_ENV_FILE

while getopts e:p: flag; do
  case "${flag}" in
    e) RELEASE_ENV_FILE=${OPTARG} ;;
    p) PROMOTION_ENV_FILE=${OPTARG} ;;
    *)
      echo "Error in command line parsing" >&2
      exit 1
      ;;
  esac
done

if [ -z "${RELEASE_ENV_FILE:-}" ] || [ -z "${PROMOTION_ENV_FILE:-}" ]; then
  echo "Missing parameters" >&2
  exit 1
fi

source "$RELEASE_ENV_FILE"
source "$PROMOTION_ENV_FILE"

printf "Release tag: %s\n" "$release_tag"
printf "Source commit: %s\n" "$resolved_commit_id"
printf "Source image tag: %s\n" "$source_sha_tag"
printf "Chart version: %s\n" "$chart_version"
printf "Released image: %s\n" "$promoted_image_uri"
