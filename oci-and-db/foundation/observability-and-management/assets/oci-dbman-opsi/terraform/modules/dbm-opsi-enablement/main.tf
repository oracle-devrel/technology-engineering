# Modular DBM + Ops Insights enablement.
#
# Each capability is gated by its own toggle and driven by for_each over the
# `targets` map, so adding a target or turning a feature off is a no-destroy
# change to the others. New capabilities should be added as additional,
# independently-gated resource blocks here.

locals {
  dbm_targets  = var.enable_database_management ? var.targets : {}
  opsi_targets = var.enable_ops_insights && var.opsi_private_endpoint_id != null ? var.targets : {}
  cred_targets = var.set_preferred_credentials ? var.targets : {}
  data_safe_targets = var.enable_data_safe && var.data_safe_private_endpoint_id != null ? var.targets : {}

  # Cartesian product of credential targets x preferred-credential slots.
  preferred_credentials = merge([
    for name, _ in local.cred_targets : {
      for slot in ["PC_READ", "PC_WRITE"] : "${name}-${slot}" => {
        target = name
        slot   = slot
      }
    }
  ]...)
}

# 1. Database Management (DIAGNOSTICS_AND_MANAGEMENT) over the DBM private endpoint.
resource "oci_database_management_database_dbm_features_management" "dbm" {
  for_each                    = local.dbm_targets
  database_id                 = each.value.database_id
  enable_database_dbm_feature = true

  feature_details {
    feature         = "DIAGNOSTICS_AND_MANAGEMENT"
    management_type = each.value.management_type

    connector_details {
      connector_type       = "PE"
      private_end_point_id = var.dbm_private_endpoint_id
    }

    database_connection_details {
      connection_credentials {
        credential_type    = "DETAILS"
        user_name          = var.monitoring_user
        password_secret_id = var.password_secret_id
        role               = "NORMAL"
      }
      connection_string {
        connection_type = "BASIC"
        port            = 1521
        protocol        = "TCP"
        service         = each.value.service_name
      }
    }
  }
}

# 2. Vault-backed Named Credential (RESOURCE_PRINCIPAL) for advanced diagnostics.
resource "oci_database_management_named_credential" "dbsnmp" {
  for_each            = local.cred_targets
  compartment_id      = var.compartment_id
  name                = "${each.key}_${var.monitoring_user}_NORMAL"
  scope               = "RESOURCE"
  type                = "ORACLE_DB"
  associated_resource = each.value.database_id

  content {
    credential_type             = "BASIC"
    user_name                   = var.monitoring_user
    role                        = "NORMAL"
    password_secret_id          = var.password_secret_id
    password_secret_access_mode = "RESOURCE_PRINCIPAL"
  }

  depends_on = [oci_database_management_database_dbm_features_management.dbm]
}

# 3. Preferred credentials PC_READ / PC_WRITE -> the named credential.
# The OCI provider exposes preferred credentials only as a data source (no
# resource), so they are wired with the dedicated CLI verb. Runs on apply and
# whenever the named credential changes. Requires the `oci` CLI on the runner
# (Cloud Shell / ORM agent) authenticated to the same tenancy.
resource "null_resource" "preferred_credential" {
  for_each = local.preferred_credentials

  triggers = {
    managed_database_id = local.cred_targets[each.value.target].database_id
    named_credential_id = oci_database_management_named_credential.dbsnmp[each.value.target].id
    slot                = each.value.slot
  }

  provisioner "local-exec" {
    command = join(" ", [
      "oci database-management preferred-credential",
      "update-preferred-credential-update-named-preferred-credential-details",
      "--managed-database-id", self.triggers.managed_database_id,
      "--credential-name", self.triggers.slot,
      "--named-credential-id", self.triggers.named_credential_id,
    ])
  }
}

# 4. Operations Insights PE co-managed Database Insight.
resource "oci_opsi_database_insight" "insight" {
  for_each                 = local.opsi_targets
  compartment_id           = var.compartment_id
  entity_source            = "PE_COMANAGED_DATABASE"
  database_id              = each.value.database_id
  database_resource_type   = each.value.database_resource_type
  deployment_type          = "VIRTUAL_MACHINE"
  opsi_private_endpoint_id  = var.opsi_private_endpoint_id

  credential_details {
    credential_type        = "CREDENTIALS_BY_VAULT"
    credential_source_name = "${each.key}-dbsnmp"
    user_name              = var.monitoring_user
    role                   = "NORMAL"
    password_secret_id     = var.password_secret_id
  }

  connection_details {
    protocol     = "TCP"
    service_name = each.value.service_name

    hosts {
      host_ip = each.value.host_ip
      port    = 1521
    }
  }

  lifecycle {
    # deployment_type is accepted on create but not returned by the API, so
    # without this TF would perpetually try to re-set it and force replacement.
    ignore_changes = [deployment_type]
  }

  depends_on = [oci_database_management_database_dbm_features_management.dbm]
}

# 5. Data Safe target-database registration (security pillar).
# Connects through the Data Safe private endpoint as the monitoring user. The
# password is plaintext in state (the API takes a password, not a Vault secret),
# so supply it via TF_VAR_data_safe_password and keep state restricted.
resource "oci_data_safe_target_database" "target" {
  for_each       = local.data_safe_targets
  compartment_id = var.compartment_id
  display_name   = each.key

  database_details {
    database_type       = "DATABASE_CLOUD_SERVICE"
    infrastructure_type = "ORACLE_CLOUD"
    db_system_id        = each.value.db_system_id
    service_name        = each.value.service_name
    listener_port       = 1521
  }

  connection_option {
    connection_type              = "PRIVATE_ENDPOINT"
    datasafe_private_endpoint_id = var.data_safe_private_endpoint_id
  }

  credentials {
    user_name = var.monitoring_user
    password  = var.data_safe_password
  }

  depends_on = [oci_database_management_database_dbm_features_management.dbm]
}
