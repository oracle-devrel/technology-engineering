locals {
  devops_project_id = var.create_devops_project ? (
    oci_devops_project.devops_project[0].id
  ) : data.oci_devops_project.existing[0].id
  devops_project_name = var.create_devops_project ? (
    var.devops_project_name
  ) : data.oci_devops_project.existing[0].name
  devops_project_compartment_id = var.create_devops_project ? (
    var.compartment_id
  ) : data.oci_devops_project.existing[0].compartment_id
  applications_enabled = var.gitops_scope == "applications_and_cluster"
  apps_repository_url  = local.applications_enabled ? (var.gitops_agent == "fluxcd" ? oci_devops_repository.apps_config_repo_flux[0].http_url : oci_devops_repository.apps_config_repo_argocd[0].http_url) : ""

  region_key               = lower([for s in data.oci_identity_region_subscriptions.oci_region_subscriptions.region_subscriptions : s if s.region_name == var.region][0].region_key)
  namespace                = data.oci_artifacts_container_configuration.ocir_config.namespace
  base_repo_path           = "repos/${var.gitops_agent}"
  repository_seed_revision = "gitops-scope-v1"
  gitops_namespace         = var.gitops_agent == "fluxcd" ? "flux-system" : "argocd"
  kube_endpoint            = "PRIVATE_ENDPOINT"
  oke_worker_nsg_ids       = try(trimspace(var.oke_worker_nsg_id), "") == "" ? [] : [var.oke_worker_nsg_id]
  flux_fleet_members = var.gitops_agent == "fluxcd" && var.enable_multicluster ? {
    (var.flux_fleet_member_name) = {
      manages_operator      = false
      activates_development = false
    }
  } : {}
}
