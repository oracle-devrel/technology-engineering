output "gitops_bootstrap_pipeline_id" {
  description = "OCI DevOps build pipeline that mirrors and installs the selected GitOps agent"
  value       = oci_devops_build_pipeline.bootstrap_gitops_agent.id
}

output "gitops_deploy_pipeline_id" {
  value = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
}

output "pipelines_repository_id" {
  value = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux[0].id : oci_devops_repository.devops_pipelines_repo_argocd[0].id
}

output "gitops_deploy_environment_id" {
  value = oci_devops_deploy_environment.oke_environment.id
}

output "gitops_deploy_artifact_ids" {
  value = concat(
    [oci_devops_deploy_artifact.gitops_bootstrap_prepare.id],
    oci_devops_deploy_artifact.flux_operator_chart[*].id,
    oci_devops_deploy_artifact.flux_operator_values[*].id,
    oci_devops_deploy_artifact.argocd_operator_chart[*].id,
    oci_devops_deploy_artifact.argocd_operator_values[*].id
  )
}

output "gitops_repository_ids" {
  description = "Runtime-readable cluster, application and optional fleet repositories"
  value = concat(
    oci_devops_repository.cluster_config_repo_flux[*].id,
    oci_devops_repository.cluster_config_repo_argocd[*].id,
    oci_devops_repository.apps_config_repo_flux[*].id,
    oci_devops_repository.apps_config_repo_argocd[*].id,
    oci_devops_repository.fleet_config_repo[*].id
  )
}

output "gitops_mirror_pipeline_id" {
  description = "OCI DevOps build pipeline that mirrors the selected GitOps agent without deploying it"
  value       = oci_devops_build_pipeline.mirror_gitops_agent.id
}

output "fleet_config_repository_url" {
  description = "Optional fleet-config repository URL"
  value       = try(oci_devops_repository.fleet_config_repo[0].http_url, null)
}

output "devops_project_id" {
  description = "OCID of the created or reused OCI DevOps project"
  value       = local.devops_project_id
}

output "devops_project_name" {
  description = "Name of the created or reused OCI DevOps project"
  value       = local.devops_project_name
}

output "devops_project_compartment_id" {
  description = "Compartment OCID of the created or reused OCI DevOps project"
  value       = local.devops_project_compartment_id
}

output "gitops_scope" {
  description = "Initial repository scope selected for this GitOps stack"
  value       = var.gitops_scope
}

output "pipelines_repository_url" {
  description = "HTTPS URL of the GitOps pipeline repository"
  value = var.gitops_agent == "fluxcd" ? (
    oci_devops_repository.devops_pipelines_repo_flux[0].http_url
  ) : oci_devops_repository.devops_pipelines_repo_argocd[0].http_url
}

output "cluster_config_repository_url" {
  description = "HTTPS URL of the selected agent's cluster-config repository"
  value = var.gitops_agent == "fluxcd" ? (
    oci_devops_repository.cluster_config_repo_flux[0].http_url
  ) : oci_devops_repository.cluster_config_repo_argocd[0].http_url
}

output "apps_config_repository_url" {
  description = "HTTPS URL of the selected agent's apps-config repository"
  value       = local.applications_enabled ? local.apps_repository_url : null
}
