#!/usr/bin/env bash
# Offline preflight: validates configuration without contacting the database.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/config.env}"
[[ -r "$CONFIG_FILE" ]] || { echo "Missing config: $CONFIG_FILE" >&2; exit 2; }
# shellcheck disable=SC1090
source "$CONFIG_FILE"

: "${DB_USER:?DB_USER is required}"
: "${DB_PASSWORD:?DB_PASSWORD is required}"
: "${BASE_CONNECT_STRING:?BASE_CONNECT_STRING is required}"
: "${AWR:=n}"
[[ "$AWR" =~ ^[YyNn]$ ]] || { echo 'FAIL: AWR must be y or n.' >&2; exit 2; }
[[ "$BASE_CONNECT_STRING" =~ \(DESCRIPTION[[:space:]]*= ]] || { echo 'FAIL: BASE_CONNECT_STRING must be a full DESCRIPTION descriptor.' >&2; exit 2; }
[[ "$BASE_CONNECT_STRING" =~ \(CONNECT_DATA[[:space:]]*= ]] || { echo 'FAIL: descriptor has no CONNECT_DATA.' >&2; exit 2; }
[[ ! "$BASE_CONNECT_STRING" =~ COLOCATION_TAG[[:space:]]*= ]] || { echo 'FAIL: remove existing COLOCATION_TAG from base descriptor.' >&2; exit 2; }

sample_tag='C_TAGGED'
sample="$(BASE_DESCRIPTOR="$BASE_CONNECT_STRING" COLOCATION_TAG_VALUE="$sample_tag" perl -0777 -e '
  $d=$ENV{BASE_DESCRIPTOR}; $t=$ENV{COLOCATION_TAG_VALUE};
  $d =~ s/(\(CONNECT_DATA\s*=)/$1(COLOCATION_TAG=$t)/i or die "CONNECT_DATA not found\n"; print $d;
')"
echo 'PASS: configuration is structurally valid.'
echo "Sample tag: $sample_tag"
echo "Descriptor shape: $(printf '%s' "$sample" | sed -E 's/(HOST=)[^)]+/\1<redacted>/Ig')"
echo 'No database connection was attempted.'
