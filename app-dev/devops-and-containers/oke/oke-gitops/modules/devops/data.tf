data "oci_artifacts_container_configuration" "ocir_config" {
  compartment_id = var.compartment_id
}

data "oci_identity_region_subscriptions" "oci_region_subscriptions" {
  tenancy_id = var.tenancy_id
}