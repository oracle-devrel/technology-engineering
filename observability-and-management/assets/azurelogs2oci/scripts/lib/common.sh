#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# common.sh – Shared helper functions for azurelogs2oci scripts
#
# Source this file at the top of every script:
#   SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
#   source "$SCRIPT_DIR/lib/common.sh"
# ─────────────────────────────────────────────────────────────

# ── Logging ──────────────────────────────────────────────────
info() { printf "ℹ️  %s\n" "$*"; }
ok()   { printf "✅ %s\n" "$*"; }
warn() { printf "⚠️  %s\n" "$*" >&2; }
err()  { printf "❌ %s\n" "$*" >&2; }

# ── Prerequisite check ───────────────────────────────────────
require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing required command: $1"
    exit 1
  fi
}

# ── Prompting ────────────────────────────────────────────────
prompt_default() {
  local prompt="$1" default="$2" var
  read -r -p "$prompt [$default]: " var
  if [[ -z "$var" ]]; then echo "$default"; else echo "$var"; fi
}

prompt_required() {
  local prompt="$1" default="${2:-}" val=""
  while true; do
    read -r -p "$prompt${default:+ [$default]}: " val
    if [[ -z "$val" ]]; then
      if [[ -n "$default" ]]; then val="$default"; break; fi
      warn "This value is required."
      continue
    fi
    break
  done
  echo "$val"
}

prompt_secret() {
  local prompt="$1" var
  read -r -s -p "$prompt: " var
  echo
  echo "$var"
}

prompt_yn() {
  local prompt="$1" default="${2:-y}" ans
  read -r -p "$prompt [$default]: " ans
  ans="${ans:-$default}"
  [[ "$ans" =~ ^[Yy] ]]
}

# ── Environment file helpers ─────────────────────────────────

# load_env [path]
#   Source .env.local (preferred) or legacy .env with tolerance for unset variables.
#   Defaults to $REPO_ROOT/.env.local if no argument given.
load_env() {
  local env_path="${1:-${REPO_ROOT:-.}/.env.local}"
  local legacy_env_path=""
  if [[ ! -f "$env_path" && "$env_path" == *.env.local ]]; then
    legacy_env_path="${env_path%.local}"
  fi
  if [[ -f "$env_path" ]]; then
    info "Loading existing values from $env_path"
    set +u; set -a
    # shellcheck disable=SC1090
    source "$env_path"
    set +a; set -u
  elif [[ -n "$legacy_env_path" && -f "$legacy_env_path" ]]; then
    info "Loading existing values from $legacy_env_path"
    set +u; set -a
    # shellcheck disable=SC1090
    source "$legacy_env_path"
    set +a; set -u
  fi
}

# update_env_var KEY VALUE [file]
#   Add or update a KEY=VALUE pair in .env.local without clobbering other entries.
#   Creates the file if it doesn't exist.
#   Uses temp-file + mv instead of sed -i for macOS/Linux portability.
update_env_var() {
  local key="$1" value="$2"
  local env_file="${3:-${REPO_ROOT:-.}/.env.local}"

  # Ensure file exists
  if [[ ! -f "$env_file" ]]; then
    touch "$env_file"
  fi

  if grep -q "^${key}=" "$env_file" 2>/dev/null; then
    # Update existing line (temp-file approach avoids sed -i portability issues)
    # Use single quotes to prevent command substitution when .env is source'd
    local tmpfile
    tmpfile="$(mktemp)"
    while IFS= read -r line || [[ -n "$line" ]]; do
      if [[ "$line" == "${key}="* ]]; then
        printf "%s='%s'\n" "${key}" "${value}"
      else
        printf '%s\n' "$line"
      fi
    done < "$env_file" > "$tmpfile"
    mv "$tmpfile" "$env_file"
  else
    # Append new entry
    printf "%s='%s'\n" "${key}" "${value}" >> "$env_file"
  fi
}
