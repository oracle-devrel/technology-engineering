# =============================================================================
# Autonomous Database Module
# =============================================================================

resource "oci_database_autonomous_database" "adb" {
  compartment_id              = var.compartment_ocid
  display_name                = "${var.resource_prefix}-${var.db_display_name}"
  db_name                     = var.db_name
  admin_password              = var.admin_password
  cpu_core_count              = var.cpu_core_count
  data_storage_size_in_gbs    = var.data_storage_size_in_gb
  db_workload                 = var.db_workload
  is_free_tier                = var.is_free_tier
  license_model               = var.license_model
  subnet_id                   = var.subnet_id
  nsg_ids                     = [var.nsg_id]
  is_auto_scaling_enabled     = true
  is_mtls_connection_required = false
  freeform_tags               = var.freeform_tags

  whitelisted_ips = []
}

# Download the ADB wallet for secure connections
resource "oci_database_autonomous_database_wallet" "wallet" {
  autonomous_database_id = oci_database_autonomous_database.adb.id
  password               = var.admin_password
  base64_encode_content  = true
  generate_type          = "SINGLE"
}
