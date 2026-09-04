#!/bin/sh
set -eu

require_env() {
  var_name="$1"
  eval "var_value=\${$var_name:-}"
  if [ -z "$var_value" ]; then
    echo "Missing required environment variable: $var_name" >&2
    exit 1
  fi
}

require_env OCI_PRIVATE_KEY_CONTENT
require_env OCI_TENANCY
require_env OCI_USER
require_env OCI_FINGERPRINT
require_env OCI_REGION

mkdir -p /root/.oci
chmod 700 /root/.oci

printf '%s\n' "$OCI_PRIVATE_KEY_CONTENT" | tr -d '\r' > /root/.oci/oci_api_key.pem
chmod 600 /root/.oci/oci_api_key.pem

cat > /root/.oci/config <<EOF
[DEFAULT]
user=$OCI_USER
fingerprint=$OCI_FINGERPRINT
tenancy=$OCI_TENANCY
region=$OCI_REGION
key_file=/root/.oci/oci_api_key.pem
EOF

export OCI_CONFIG_FILE=/root/.oci/config

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "${UVICORN_WORKERS:-2}"
