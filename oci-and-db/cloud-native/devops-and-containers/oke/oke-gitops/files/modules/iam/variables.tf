variable "compartment_id" {}
variable "policy_compartment_id" { type = string }
variable "dynamic_group_name" {}
variable "iam_domain_id" {}
variable "devops_policy_name" {}
variable "network_compartment_id" {}
variable "oke_compartment_id" {}

variable "project_id" { type = string }
variable "build_pipeline_ids" {
  type = list(string)
  validation {
    condition     = length(var.build_pipeline_ids) == 2
    error_message = "Execution IAM requires the exact mirror and bootstrap pipeline IDs."
  }
}
variable "bootstrap_pipeline_id" { type = string }
variable "deploy_pipeline_id" { type = string }
variable "pipelines_repository_id" { type = string }
variable "deploy_environment_id" { type = string }
variable "deploy_artifact_ids" { type = list(string) }
variable "oke_cluster_id" { type = string }
variable "use_network_security_groups" { type = bool }
variable "ocir_repo_path_prefix" {
  type = string
  validation {
    condition     = can(regex("^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$", var.ocir_repo_path_prefix))
    error_message = "The execution registry prefix must be a lowercase path without IAM wildcards."
  }
}
variable "secret_ids" {
  type = list(string)
  validation {
    condition     = alltrue([for id in var.secret_ids : can(regex("^ocid1\\.vaultsecret\\.[A-Za-z0-9.-]+$", id))])
    error_message = "Secret access must be an explicit allowlist of Vault secret OCIDs."
  }
}
