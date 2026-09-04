output "gitops_bootstrap_pipeline_id" {
  description = "OCI DevOps build pipeline that mirrors and installs the selected GitOps agent"
  value       = oci_devops_build_pipeline.bootstrap_gitops_agent.id
}

output "gitops_mirror_pipeline_id" {
  description = "OCI DevOps build pipeline that mirrors the selected GitOps agent without deploying it"
  value       = oci_devops_build_pipeline.mirror_gitops_agent.id
}

output "fleet_config_repository_url" {
  description = "Optional fleet-config repository URL"
  value       = try(oci_devops_repository.fleet_config_repo[0].http_url, null)
}
