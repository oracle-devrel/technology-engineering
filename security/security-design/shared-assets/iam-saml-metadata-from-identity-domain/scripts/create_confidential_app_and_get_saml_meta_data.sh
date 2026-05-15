#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------------------------
# Create a confidential OAuth client in an OCI Identity Domain (IDCS),
# mint a client_credentials access token, and fetch /fed/v1/metadata (SAML).
# Optionally deactivate+delete the app afterwards (default).
#
# Usage (examples):
#   IDCS_ENDPOINT="https://idcs-<hash>.identity.oraclecloud.com" \
#   PROFILE="DEFAULT" \
#   KEEP_APP="true" \
#   bash create_confidential_app_and_get_saml_meta_data.sh
#
# Notes:
# - Do NOT put "urn:opc:idm:__myscopes__" in allowedScopes; it's a pseudo-scope
#   used only at token request time.
# - For least privilege, grant the client only the admin role(s) needed.
# ------------------------------------------------------------------------------

umask 077

APP_NAME="${APP_NAME:-saml-metadata-client}"
IDCS_ENDPOINT="${IDCS_ENDPOINT:-}"   # e.g. https://idcs-<hash>.identity.oraclecloud.com
SCOPE="${SCOPE:-urn:opc:idm:__myscopes__}"
OUT_XML="${OUT_XML:-oci_idcs_metadata.xml}"
PROFILE="${PROFILE:-}"
KEEP_APP="${KEEP_APP:-false}"

# Optional admin creds for cleanup (preferred)
ADMIN_ACCESS_TOKEN="${ADMIN_ACCESS_TOKEN:-}"
ADMIN_CLIENT_ID="${ADMIN_CLIENT_ID:-}"
ADMIN_CLIENT_SECRET="${ADMIN_CLIENT_SECRET:-}"
ADMIN_SCOPE="${ADMIN_SCOPE:-urn:opc:idm:__myscopes__}"

usage() {
  cat <<EOF
Usage:
  IDCS_ENDPOINT="https://idcs-<hash>.identity.oraclecloud.com" \\
  PROFILE="oci_profile_name" \\
  [ADMIN_ACCESS_TOKEN=... | ADMIN_CLIENT_ID=... ADMIN_CLIENT_SECRET=...] \\
  bash create_confidential_app_and_get_saml_meta_data.sh
Env:
  APP_NAME, SCOPE, OUT_XML, PROFILE, KEEP_APP
  ADMIN_ACCESS_TOKEN         (preferred) Bearer token with admin rights (Identity Domain Admin)
  ADMIN_CLIENT_ID/SECRET     (alt) admin confidential app creds to mint an admin token
  ADMIN_SCOPE                (default: urn:opc:idm:__myscopes__)
EOF
}

[[ -z "${IDCS_ENDPOINT}" ]] && { usage; echo "ERROR: IDCS_ENDPOINT is required." >&2; exit 1; }

need(){ command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' is required." >&2; exit 1; }; }
need oci; need jq; need curl

profile_arg=(); [[ -n "$PROFILE" ]] && profile_arg=(--profile "$PROFILE")

APP_JSON="$(mktemp -t app.json.XXXXXX)"
REGEN_JSON="$(mktemp -t regen.json.XXXXXX)"
DEACT_OUT="$(mktemp -t deact.out.XXXXXX)"
trap 'rm -f "$APP_JSON" "$REGEN_JSON" "$DEACT_OUT"' EXIT

APP_ID_FOR_CLEANUP=""
APP_VERSION_FOR_CLEANUP=""
ACCESS_TOKEN=""          # app token for /fed/v1/metadata
ADMIN_TOKEN=""           # admin token for cleanup (if available)

# --- helpers ------------------------------------------------------------------

b64_oneline() { base64 | tr -d '\n'; }

urlenc() { jq -sRr @uri <<<"$1"; }

get_token_cc () {
  # args: client_id client_secret scope -> prints access_token
  local cid="$1" sec="$2" sc="${3:-urn:opc:idm:__myscopes__}"
  local basic
  basic="$(printf '%s:%s' "$cid" "$sec" | b64_oneline)"
  curl -sSf -X POST "$IDCS_ENDPOINT/oauth2/v1/token" \
    -H "Authorization: Basic $basic" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&scope=$(urlenc "$sc")" \
  | jq -r '.access_token // empty'
}

cleanup_app() {
  if [[ "${KEEP_APP}" != "true" && -n "${APP_ID_FOR_CLEANUP}" ]]; then
    echo "Cleaning up: deactivating then deleting app ${APP_ID_FOR_CLEANUP} ..."

    # Pick an admin token: explicit ADMIN_ACCESS_TOKEN, or mint from ADMIN_CLIENT_ID/SECRET, else fall back to app token (may fail)
    if [[ -n "$ADMIN_ACCESS_TOKEN" ]]; then
      ADMIN_TOKEN="$ADMIN_ACCESS_TOKEN"
    elif [[ -n "$ADMIN_CLIENT_ID" && -n "$ADMIN_CLIENT_SECRET" ]]; then
      echo "Minting admin token for cleanup ..."
      ADMIN_TOKEN="$(get_token_cc "$ADMIN_CLIENT_ID" "$ADMIN_CLIENT_SECRET" "$ADMIN_SCOPE" || true)"
    fi
    [[ -z "$ADMIN_TOKEN" ]] && ADMIN_TOKEN="$ACCESS_TOKEN"

    # Deactivate with SCIM PATCH + If-Match: <meta.version>
    if [[ -n "$ADMIN_TOKEN" ]]; then
      # body: replace active -> false
      read -r -d '' PATCH_BODY <<'JSON' || true
{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    { "op": "replace", "path": "active", "value": false }
  ]
}
JSON
      if [[ -z "$APP_VERSION_FOR_CLEANUP" ]]; then
        echo "Warning: missing meta.version; deactivation may fail without If-Match." >&2
      fi

      # Use -f but don't kill the script; we want to try delete regardless
      http_code="$(curl -sS -o "$DEACT_OUT" -w "%{http_code}" -X PATCH \
        "$IDCS_ENDPOINT/admin/v1/Apps/$APP_ID_FOR_CLEANUP" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/scim+json" \
        ${APP_VERSION_FOR_CLEANUP:+ -H "If-Match: ${APP_VERSION_FOR_CLEANUP}"} \
        --data-binary "$PATCH_BODY" || true)"

      if [[ "$http_code" =~ ^2 ]]; then
        echo "App ${APP_ID_FOR_CLEANUP} deactivated."
      else
        echo "Warning: failed to deactivate app (HTTP $http_code)." >&2
        head -n 40 "$DEACT_OUT" >&2 || true
      fi
    else
      echo "Warning: no token available for deactivation; skipping." >&2
    fi

    # Delete with OCI CLI (works once inactive)
    if oci identity-domains app delete \
         --endpoint "$IDCS_ENDPOINT" \
         --app-id "$APP_ID_FOR_CLEANUP" \
         --force \
         "${profile_arg[@]}" >/dev/null 2>&1; then
      echo "App ${APP_ID_FOR_CLEANUP} deleted."
    else
      echo "Warning: failed to delete app ${APP_ID_FOR_CLEANUP}." >&2
    fi
  fi
}
trap 'cleanup_app' EXIT

# --- create app ---------------------------------------------------------------

cat >"$APP_JSON" <<'JSON'
{
  "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:App"],
  "displayName": "__APP_NAME__",
  "description": "CLI-created app to call /fed/v1/metadata",
  "isOAuthClient": true,
  "clientType": "confidential",
  "active": true,
  "allowedGrants": ["client_credentials"],
  "basedOnTemplate": { "value": "CustomWebAppTemplateId" }
}
JSON
# NOTE: Intentionally NO "allowedScopes". "__myscopes__" is NOT grantable.

sed -i.bak "s/__APP_NAME__/${APP_NAME//\//\\/}/" "$APP_JSON" && rm -f "$APP_JSON.bak"

echo "Creating confidential app '${APP_NAME}' in ${IDCS_ENDPOINT} ..."
APP_NODE="$(
  oci identity-domains app create \
    --endpoint "$IDCS_ENDPOINT" \
    --from-json "file://$APP_JSON" \
    "${profile_arg[@]}" \
    --query 'data' \
    --output json
)"

# Parse required fields
APP_ID="$(jq -r '.id // empty' <<<"$APP_NODE")"
CLIENT_ID="$(
  jq -r '
    (."urn:ietf:params:scim:schemas:oracle:idcs:extension:oauthclient:App".clientId // .clientId // .name // empty)
  ' <<<"$APP_NODE"
)"
CREATED_SECRET="$(jq -r '."client-secret" // empty' <<<"$APP_NODE")"
APP_VERSION_FOR_CLEANUP="$(jq -r '.meta.version // empty' <<<"$APP_NODE")"

if [[ -z "$APP_ID" || -z "$CLIENT_ID" ]]; then
  echo "ERROR: Failed to parse APP_ID/CLIENT_ID." >&2
  echo "Full response follows for debugging:" >&2
  echo "$APP_NODE" >&2
  exit 1
fi
APP_ID_FOR_CLEANUP="$APP_ID"

echo "Created app: APP_ID=${APP_ID}"
echo "Client ID    : ${CLIENT_ID}"

# --- get secret ---------------------------------------------------------------

if [[ -n "$CREATED_SECRET" && "$CREATED_SECRET" != "null" ]]; then
  CLIENT_SECRET="$CREATED_SECRET"
  echo "Client secret returned by create (using that)."
else
  echo "Regenerating client secret ..."
  cat >"$REGEN_JSON" <<JSON
{
  "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:AppClientSecretRegenerator"],
  "appId": "${APP_ID}"
}
JSON
  SECRET_OUT="$(oci identity-domains app-client-secret-regenerator create \
    --endpoint "$IDCS_ENDPOINT" \
    --from-json "file://$REGEN_JSON" \
    "${profile_arg[@]}")"
  CLIENT_SECRET="$(jq -r '.clientSecret // empty' <<<"$SECRET_OUT")"
  [[ -z "$CLIENT_SECRET" ]] && { echo "ERROR: Failed to obtain clientSecret."; exit 1; }
fi

# --- mint app token (for metadata) -------------------------------------------

BASIC_AUTH="$(printf '%s:%s' "$CLIENT_ID" "$CLIENT_SECRET" | b64_oneline)"
echo "Requesting OAuth2 token (client_credentials) for scope: $SCOPE ..."
ENC_SCOPE="$(urlenc "${SCOPE:-urn:opc:idm:__myscopes__}")"
ACCESS_TOKEN="$(
  curl -sSf -X POST "$IDCS_ENDPOINT/oauth2/v1/token" \
    -H "Authorization: Basic $BASIC_AUTH" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "grant_type=client_credentials&scope=${ENC_SCOPE}" \
  | jq -r '.access_token // empty'
)"
[[ -z "$ACCESS_TOKEN" ]] && { echo "ERROR: Failed to obtain access_token."; exit 1; }
echo "Access token acquired."

# --- fetch metadata -----------------------------------------------------------

echo "Fetching SAML metadata ..."
http_code="$(curl -sSfo "$OUT_XML" -w '%{http_code}' \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$IDCS_ENDPOINT/fed/v1/metadata")" || true

if [[ ! "$http_code" =~ ^2 ]]; then
  echo "ERROR: Metadata request failed (HTTP $http_code)." >&2
  [[ -s "$OUT_XML" ]] && head -n 40 "$OUT_XML" >&2
  exit 1
fi

# Quick payload sanity (catch HTML/JSON error pages)
if ! head -n1 "$OUT_XML" | grep -q '<md:EntityDescriptor'; then
  echo "ERROR: Unexpected metadata payload (not SAML XML)." >&2
  head -n 40 "$OUT_XML" >&2
  exit 1
fi

# --- results ------------------------------------------------------------------

MASKED_SECRET="${CLIENT_SECRET:0:4}...${CLIENT_SECRET: -4}"
echo "---------------------------------------------"
echo "SUCCESS"
echo "Profile       : ${PROFILE:-<default>}"
echo "IDCS_ENDPOINT : $IDCS_ENDPOINT"
echo "APP_ID        : $APP_ID"
echo "CLIENT_ID     : $CLIENT_ID"
echo "CLIENT_SECRET : $MASKED_SECRET   (store securely!)"
echo "METADATA FILE : $OUT_XML"
if [[ "${KEEP_APP}" == "true" ]]; then
  echo "Cleanup       : SKIPPED (KEEP_APP=true)"
  echo
  echo "To refresh metadata later with this client, mint a token and call:"
  echo "  curl -sSf -X POST \"$IDCS_ENDPOINT/oauth2/v1/token\" \\"
  echo "    -H \"Authorization: Basic \$(printf '%s:%s' '$CLIENT_ID' '***' | base64 | tr -d '\\n')\" \\"
  echo "    -H \"Content-Type: application/x-www-form-urlencoded\" \\"
  echo "    -d \"grant_type=client_credentials&scope=$(urlenc "$SCOPE")\" \\"
  echo "  | jq -r '.access_token' | xargs -I{} curl -sSf -H \"Authorization: Bearer {}\" \\"
  echo "       \"$IDCS_ENDPOINT/fed/v1/metadata\" > \"$OUT_XML\""
else
  echo "Cleanup       : App scheduled for deactivation+deletion now."
  cleanup_app
  APP_ID_FOR_CLEANUP=""
fi
echo "---------------------------------------------"
