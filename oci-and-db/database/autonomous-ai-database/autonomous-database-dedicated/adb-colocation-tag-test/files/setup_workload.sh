#!/usr/bin/env bash
# Creates the workload objects using SQLcl. Run once after editing config.env.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${1:-$SCRIPT_DIR/config.env}"
[[ -r "$CONFIG_FILE" ]] || { echo "Missing config: $CONFIG_FILE" >&2; exit 2; }
# shellcheck disable=SC1090
source "$CONFIG_FILE"
: "${DB_USER:?}"; : "${DB_PASSWORD:?}"; : "${BASE_CONNECT_STRING:?}"
SQL_BIN="${SQL_BIN:-sql}"; command -v "$SQL_BIN" >/dev/null || { echo "SQLcl executable not found: $SQL_BIN" >&2; exit 2; }
"$SQL_BIN" -s /nolog <<SQL
whenever oserror exit 9
whenever sqlerror exit sql.sqlcode
connect ${DB_USER}/"${DB_PASSWORD}"@${BASE_CONNECT_STRING}
@$SCRIPT_DIR/setup_workload.sql
exit
SQL
