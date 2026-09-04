locals {
  git_username       = "${data.oci_identity_tenancy.current_tenancy.name}/${data.oci_identity_user.current_user.name}"
  application_config = jsondecode(var.applications)
  application_count  = length(local.application_config)
  component_count = length(flatten([
    for application in local.application_config : application.components
  ]))
  estimated_devops_resources = {
    repositories = 1 + local.application_count + local.component_count + (var.enable_cluster_admin ? 1 : 0)
    build_pipelines = local.application_count + (3 * local.component_count) + (
      var.enable_cluster_admin ? 3 : 0
    )
    deployment_pipelines = (2 * local.application_count) + (2 * local.component_count) + (
      var.enable_cluster_admin ? 4 : 0
    )
    deployment_stages = 1 + (5 * local.application_count) + (9 * local.component_count) + (
      var.enable_cluster_admin ? 6 : 0
    )
  }
}
