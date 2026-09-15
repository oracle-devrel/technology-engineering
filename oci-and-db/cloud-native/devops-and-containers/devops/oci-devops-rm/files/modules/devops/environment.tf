resource "oci_devops_deploy_environment" "oke_environment" {
  count = local.oke_environments_required ? 1 : 0

  deploy_environment_type = "OKE_CLUSTER"
  project_id              = local.devops_project_id
  cluster_id              = var.oke_cluster_id
  display_name            = data.oci_containerengine_cluster.oke_cluster[0].name
  description             = "Pre-prod OKE cluster for Helm delivery"

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

resource "oci_devops_deploy_environment" "prod_oke_environment" {
  count = local.oke_environments_required ? 1 : 0

  deploy_environment_type = "OKE_CLUSTER"
  project_id              = local.devops_project_id
  cluster_id              = local.prod_oke_cluster_id
  display_name            = data.oci_containerengine_cluster.prod_oke_cluster[0].name
  description             = "Production OKE cluster for release deployments"

  network_channel {
    network_channel_type = "PRIVATE_ENDPOINT_CHANNEL"
    subnet_id            = local.prod_oke_worker_subnet_id
    nsg_ids              = local.prod_oke_worker_nsg_ids
  }

  lifecycle {
    ignore_changes = [
      display_name,
      description
    ]
  }
}
