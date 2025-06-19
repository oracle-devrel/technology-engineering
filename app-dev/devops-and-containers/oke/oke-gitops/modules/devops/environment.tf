resource "oci_devops_deploy_environment" "oke_environment_private" {
  deploy_environment_type = "OKE_CLUSTER"
  project_id              = oci_devops_project.devops_project.id
  cluster_id = var.oke_cluster_id
  display_name = var.oke_environment_name
  description = var.oke_environment_description
  network_channel {
    network_channel_type = "PRIVATE_ENDPOINT_CHANNEL"
    subnet_id            = var.oke_worker_subnet_id
    nsg_ids = var.oke_worker_nsg_id != null ? [var.oke_worker_nsg_id] : []
  }
  count = var.is_oke_cluster_private ? 1 : 0
}

resource "oci_devops_deploy_environment" "oke_environment_public" {
  deploy_environment_type = "OKE_CLUSTER"
  project_id              = oci_devops_project.devops_project.id
  cluster_id = var.oke_cluster_id
  display_name = var.oke_environment_name
  description = var.oke_environment_description
  count = var.is_oke_cluster_private ? 0 : 1
}