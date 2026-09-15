data "oci_devops_project" "existing" {
  count = var.create_devops_project ? 0 : 1

  project_id = var.existing_devops_project_id
}

data "oci_artifacts_container_configuration" "ocir_config" {
  compartment_id = local.devops_project_compartment_id
}

data "oci_identity_region_subscriptions" "region_subscriptions" {
  tenancy_id = var.tenancy_id
}

data "oci_containerengine_cluster" "oke_cluster" {
  count = local.oke_environments_required ? 1 : 0

  cluster_id = var.oke_cluster_id
}

data "oci_containerengine_cluster" "prod_oke_cluster" {
  count = local.oke_environments_required ? 1 : 0

  cluster_id = local.prod_oke_cluster_id
}
