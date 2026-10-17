output "git_username" {
  description = "Bootstrap-only OCI DevOps Git username used by Resource Manager for initial repository seeding"
  value       = local.git_username
}

output "devops_project_id" {
  description = "OCID of the created or reused OCI DevOps project"
  value       = module.devops.devops_project_id
}

output "devops_project_name" {
  description = "Name of the created or reused OCI DevOps project"
  value       = module.devops.devops_project_name
}

output "gitops_scope" {
  description = "Initial GitOps repository scope"
  value       = module.devops.gitops_scope
}

output "pipelines_repository_url" {
  description = "HTTPS URL of the configured GitOps pipelines repository"
  value       = module.devops.pipelines_repository_url
}

output "cluster_config_repository_url" {
  description = "HTTPS URL of the cluster-config repository"
  value       = module.devops.cluster_config_repository_url
}

output "apps_config_repository_url" {
  description = "HTTPS URL of the apps-config repository"
  value       = module.devops.apps_config_repository_url
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
  value       = "${var.create_automatic_credentials ? "Runtime credential secrets are configured as bootstrap pipeline defaults." : "Create separate read-only Git and OCIR JSON credentials in OCI Vault and set git_read_credentials_secret_ocid and registry_pull_secret_ocid on bootstrap-gitops-agent."} Run bootstrap-gitops-agent. After its triggered install-gitops-agent deployment succeeds, clone cluster-config and apply its generated bootstrap manifest as documented in the repository README. Use mirror-gitops-agent only for later chart mirroring and self-managed upgrades."
}

output "automatic_credentials" {
  description = "Generated runtime credential references; token values are not exposed"
  value = var.create_automatic_credentials ? {
    vault_id                         = oci_kms_vault.credentials[0].id
    key_id                           = oci_kms_key.credentials[0].id
    compartment_id                   = local.credentials_compartment_id
    git_read_credentials_secret_ocid = oci_vault_secret.automation["git"].id
    registry_pull_secret_ocid        = oci_vault_secret.automation["pull"].id
    policy_id                        = oci_identity_policy.automation[0].id
    policy_name                      = oci_identity_policy.automation[0].name
  } : null
}
