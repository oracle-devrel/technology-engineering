locals {
  region_key               = lower([for s in data.oci_identity_region_subscriptions.oci_region_subscriptions.region_subscriptions : s if s.region_name == var.region][0].region_key)
  namespace                = data.oci_artifacts_container_configuration.ocir_config.namespace
  base_repo_path           = "repos/${var.gitops_agent}"
  repository_seed_revision = "manual-flux-fleet-v3"
  gitops_namespace         = var.gitops_agent == "fluxcd" ? "flux-system" : "argocd"
  kube_endpoint            = "PRIVATE_ENDPOINT"
  oke_worker_nsg_ids       = try(trimspace(var.oke_worker_nsg_id), "") == "" ? [] : [var.oke_worker_nsg_id]
  legacy_git_identity      = join("/", slice(split("/", var.git_username), 1, length(split("/", var.git_username))))
  legacy_ocir_username     = "${local.namespace}/${local.legacy_git_identity}"
  flux_fleet_members = var.gitops_agent == "fluxcd" && var.enable_multicluster ? {
    (var.flux_fleet_member_name) = {
      manages_operator      = false
      activates_development = false
    }
  } : {}
}
