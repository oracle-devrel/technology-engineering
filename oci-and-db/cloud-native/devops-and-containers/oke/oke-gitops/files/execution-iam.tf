variable "execution_secret_ids" {
  description = "Manual-mode Vault secret OCIDs the installer may read in the DevOps project compartment. Set the same IDs as pipeline credential parameters. Empty grants no secret access; automatic mode uses only its two generated secrets."
  type        = list(string)
  default     = []
}

output "execution_iam" {
  description = "Execution principals, exact membership rules, and rendered policies for audit and functional probes"
  value = var.create_iam ? {
    principals               = module.iam[0].principals
    build_matching_rule      = module.iam[0].build_matching_rule
    bootstrap_matching_rule  = module.iam[0].bootstrap_matching_rule
    deployment_matching_rule = module.iam[0].deployment_matching_rule
    statements               = module.iam[0].statements
    bootstrap_pipeline_id    = module.devops.gitops_bootstrap_pipeline_id
    mirror_pipeline_id       = module.devops.gitops_mirror_pipeline_id
    deployment_pipeline_id   = module.devops.gitops_deploy_pipeline_id
    pipelines_repository_id  = module.devops.pipelines_repository_id
  } : null
}
