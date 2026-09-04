output "git_username" {
  description = "Bootstrap-only OCI DevOps Git username used by Resource Manager for initial repository seeding"
  value       = local.git_username
}

output "gitops_bootstrap_pipeline_id" {
  description = "OCI DevOps build pipeline that mirrors and installs the selected GitOps agent"
  value       = module.devops.gitops_bootstrap_pipeline_id
}

output "gitops_mirror_pipeline_id" {
  description = "OCI DevOps mirror-only build pipeline used for self-managed upgrades"
  value       = module.devops.gitops_mirror_pipeline_id
}

output "fleet_config_repository_url" {
  description = "URL of fleet-config when optional multi-cluster support is enabled"
  value       = module.devops.fleet_config_repository_url
}

output "next_steps" {
  description = "How to install the agent and start Git reconciliation"
  value       = "Create separate read-only Git and OCIR JSON credentials in OCI Vault. Run bootstrap-gitops-agent with git_read_credentials_secret_ocid and registry_pull_secret_ocid set to their Secret OCIDs. After its triggered install-gitops-agent deployment succeeds, clone cluster-config and apply its generated bootstrap manifest as documented in the repository README. Use mirror-gitops-agent only for later chart mirroring and self-managed upgrades."
}
