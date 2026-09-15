locals {
  application_delivery_enabled = var.application_delivery_mode == "oci_devops"
  build_only_enabled           = var.application_delivery_mode == "build_only"
  cluster_admin_enabled        = var.enable_cluster_admin
  oke_environments_required    = local.application_delivery_enabled || local.cluster_admin_enabled

  git_username       = "${data.oci_identity_tenancy.current_tenancy.name}/${data.oci_identity_user.current_user.name}"
  application_config = jsondecode(var.applications)
  application_count  = length(local.application_config)
  component_count = length(flatten([
    for application in local.application_config : application.components
  ]))
  estimated_devops_resources = {
    repositories = 1 + local.component_count + (local.application_delivery_enabled ? local.application_count : 0) + (var.enable_cluster_admin ? 1 : 0)
    build_pipelines = (local.application_delivery_enabled ? local.application_count + (3 * local.component_count) : 2 * local.component_count) + (
      var.enable_cluster_admin ? 3 : 0
    )
    deployment_pipelines = (local.application_delivery_enabled ? (2 * local.application_count) + (2 * local.component_count) : 0) + (
      var.enable_cluster_admin ? 4 : 0
    )
    deployment_stages = (local.application_delivery_enabled ? 1 + (5 * local.application_count) + (9 * local.component_count) : 0) + (
      var.enable_cluster_admin ? 6 : 0
    )
  }
}
