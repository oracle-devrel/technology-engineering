data "oci_secrets_secretbundle" "password_secret" {
  secret_id = var.password_secret_id
}

output "password_secret_content" {
  value = data.oci_secrets_secretbundle.password_secret.secret_bundle_content.0.content
}