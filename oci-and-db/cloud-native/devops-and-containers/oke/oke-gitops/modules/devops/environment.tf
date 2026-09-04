resource "oci_devops_deploy_environment" "oke_environment" {
  deploy_environment_type = "OKE_CLUSTER"
  project_id              = oci_devops_project.devops_project.id
  cluster_id              = var.oke_cluster_id
  display_name            = var.oke_environment_name
  description             = coalesce(var.oke_environment_description, "Private-endpoint OKE environment for GitOps agent installation")

  network_channel {
    network_channel_type = "PRIVATE_ENDPOINT_CHANNEL"
    subnet_id            = var.oke_worker_subnet_id
    nsg_ids              = local.oke_worker_nsg_ids
  }

  lifecycle {
    ignore_changes = [
      display_name,
      description
    ]
  }
}
