REGISTRY="ocir.eu-frankfurt-1.oci.oraclecloud.com"
USERNAME="<OCI_REGISTRY_USERNAME>"
PASSWORD="<OCI_REGISTRY_AUTH_TOKEN>"

AUTH="$(printf '%s:%s' "$USERNAME" "$PASSWORD" | base64 | tr -d '\n')"

cat > dockerconfig.json <<EOF
{
  "auths": {
    "$REGISTRY": {
      "username": "$USERNAME",
      "password": "$PASSWORD",
      "auth": "$AUTH"
    }
  }
}
EOF
