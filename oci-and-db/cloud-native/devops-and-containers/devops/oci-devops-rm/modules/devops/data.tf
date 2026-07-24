data "oci_artifacts_container_configuration" "ocir_config" {
  compartment_id = var.compartment_id
}

data "oci_identity_region_subscriptions" "region_subscriptions" {
  tenancy_id = var.tenancy_id
}

data "oci_containerengine_cluster" "oke_cluster" {
  cluster_id = var.oke_cluster_id
}

data "oci_containerengine_cluster" "prod_oke_cluster" {
  cluster_id = local.prod_oke_cluster_id
}
