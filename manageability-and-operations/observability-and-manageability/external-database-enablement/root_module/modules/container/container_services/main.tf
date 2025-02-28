resource "oci_database_external_container_database_management" "this" {
  count = var.enable_database_management_cdb == "enable" ? 1 : 0

  external_container_database_id = var.external_container_id
  external_database_connector_id = var.external_container_connector_id
  license_model                  = var.external_container_database_management_license
  enable_management              = true
}

resource "time_static" "database_management_cdb_status_update" {
  triggers = {
    status_update = try(tobool(oci_database_external_container_database_management.this[0].enable_management), false)
  }
}

resource "oci_database_externalcontainerdatabases_stack_monitoring" "this" {
  count = var.enable_stack_monitoring_cdb == "enable" ? 1 : 0

  external_container_database_id = var.external_container_id
  external_database_connector_id = var.external_container_connector_id
  enable_stack_monitoring        = true

  depends_on = [oci_database_external_container_database_management.this]
}

resource "oci_stack_monitoring_monitored_resources_search" "external_cdb_search" {
  count = var.enable_stack_monitoring_cdb == "enable" ? 1 : 0

  compartment_id = var.compartment_ocid
  external_id    = var.external_container_id
  state          = "ACTIVE"
  type           = "OCI_ORACLE_CDB"

  depends_on = [oci_database_externalcontainerdatabases_stack_monitoring.this]
}

resource "oci_stack_monitoring_discovery_job" "db_system_refresh_job" {
  count = var.enable_stack_monitoring_cdb == "enable" && var.enable_stack_monitoring_asm == "disable" ? 1 : 0

  compartment_id = var.compartment_ocid
  discovery_details {
    agent_id = var.external_database_connector_agent_id

    properties {
      properties_map = {
        "allow_delete_resources" : "true",
        "resource_id" : "${element(oci_stack_monitoring_monitored_resources_search.external_cdb_search.0.items, 0).id}",
      }
    }

    resource_name = var.external_container_display_name
    resource_type = "ORACLE_DATABASE"
  }

  discovery_type = "REFRESH"
}

resource "oci_stack_monitoring_discovery_job" "db_system_asm_refresh_job" {
  count = var.enable_stack_monitoring_cdb == "enable" && var.enable_stack_monitoring_asm == "enable" ? 1 : 0

  compartment_id = var.compartment_ocid
  discovery_details {
    agent_id = var.external_database_connector_agent_id

    properties {
      properties_map = {
        "allow_delete_resources" : "true",
        "resource_id" : "${element(oci_stack_monitoring_monitored_resources_search.external_cdb_search.0.items, 0).id}",
        "is_asm_discovery" : "true",
        "asm_host" : "${var.asm_hostname}",
        "asm_port" : "${var.asm_port}",
        "asm_service_name" : "${var.asm_service}",
      }
    }

    credentials {
      items {
        credential_name = base64encode("ASMPasswordInVault")
        credential_type = base64encode("SSL_SECRET_ID")
        properties {
          properties_map = {
            "ASMRole" : base64encode("${var.asm_credentials_role}"),
            "ASMUserName" : base64encode("${var.asm_credentials_username}"),
            "PasswordSecretId" : base64encode("${var.asm_credentials_password_secret_id}")
          }
        }
      }
    }

    resource_name = var.external_container_display_name
    resource_type = "ORACLE_DATABASE"
  }

  discovery_type = "REFRESH"
}

output "database_management_cdb_status" {
  value = time_static.database_management_cdb_status_update.triggers.status_update
}