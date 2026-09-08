data "oci_devops_project" "existing" {
  count = var.create_devops_project ? 0 : 1

  project_id = trimspace(var.existing_devops_project_id)
}

data "oci_artifacts_container_configuration" "ocir_config" {
  compartment_id = local.devops_project_compartment_id
}

data "oci_identity_region_subscriptions" "oci_region_subscriptions" {
  tenancy_id = var.tenancy_id
}
