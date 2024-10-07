resource "oci_database_external_container_database" "this" {
  compartment_id = var.compartment_ocid
  display_name   = var.external_container_database_display_name
}

resource "oci_database_external_database_connector" "container_connector" {
  connection_credentials {
    credential_name = var.external_cdb_connector_connection_credentials_credential_name
    credential_type = var.external_cdb_connector_connection_credentials_credential_type
    password        = var.external_cdb_connector_connection_credentials_password
    role            = var.external_cdb_connector_connection_credentials_role
    ssl_secret_id   = var.ssl_secret_id
    username        = var.external_cdb_connector_connection_credentials_username
  }
  connection_string {
    hostname = var.external_database_connector_connection_string_hostname
    port     = var.external_database_connector_connection_string_port
    protocol = var.external_database_connector_connection_string_protocol
    service  = var.external_cdb_connector_connection_string_service
  }
  connector_agent_id   = var.external_database_connector_agent_id
  display_name         = "${var.external_container_database_display_name}_connector"
  external_database_id = oci_database_external_container_database.this.id
}

output "external_container_display_name" {
  value = oci_database_external_container_database.this.display_name
}

output "external_container_id" {
  value = oci_database_external_container_database.this.id
}

output "external_container_connector_id" {
  value = oci_database_external_database_connector.container_connector.id
}