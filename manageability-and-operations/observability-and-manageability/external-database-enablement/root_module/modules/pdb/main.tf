resource "oci_database_external_pluggable_database" "that" {
  compartment_id                 = var.compartment_ocid
  display_name                   = var.external_pluggable_database_display_name
  external_container_database_id = var.oci_database_external_container_database_id
}

resource "oci_database_external_database_connector" "pdb_connector" {
  connection_credentials {
    credential_name = var.external_pdb_connector_connection_credentials_credential_name
    credential_type = var.external_pdb_connector_connection_credentials_credential_type
    password        = var.external_pdb_connector_connection_credentials_password
    role            = var.external_pdb_connector_connection_credentials_role
    ssl_secret_id   = var.ssl_secret_id
    username        = var.external_pdb_connector_connection_credentials_username
  }
  connection_string {
    hostname = var.external_database_connector_connection_string_hostname
    port     = var.external_database_connector_connection_string_port
    protocol = var.external_database_connector_connection_string_protocol
    service  = var.external_pdb_connector_connection_string_service
  }
  connector_agent_id   = var.external_database_connector_agent_id
  display_name         = "${var.external_pluggable_database_display_name}_connector"
  external_database_id = oci_database_external_pluggable_database.that.id
}

resource "oci_database_external_pluggable_database_management" "that" {
  count = var.enable_database_management_pdb == "enable" ? 1 : 0

  external_database_connector_id = oci_database_external_database_connector.pdb_connector.id
  external_pluggable_database_id = oci_database_external_pluggable_database.that.id
  enable_management              = true

  depends_on = [oci_database_external_pluggable_database_operations_insights_management.that, oci_database_externalpluggabledatabases_stack_monitoring.that]
}

resource "oci_database_externalpluggabledatabases_stack_monitoring" "that" {
  count = var.enable_stack_monitoring_pdb == "enable" ? 1 : 0

  external_pluggable_database_id = oci_database_external_pluggable_database.that.id
  external_database_connector_id = oci_database_external_database_connector.pdb_connector.id
  enable_stack_monitoring        = true

  depends_on = [oci_database_external_pluggable_database_operations_insights_management.that]
}

resource "oci_database_external_pluggable_database_operations_insights_management" "that" {
  count = var.enable_operations_insights_pdb == "enable" ? 1 : 0

  external_database_connector_id = oci_database_external_database_connector.pdb_connector.id
  external_pluggable_database_id = oci_database_external_pluggable_database.that.id
  enable_operations_insights     = true
}