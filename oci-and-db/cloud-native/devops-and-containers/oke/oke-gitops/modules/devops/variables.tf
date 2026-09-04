variable "compartment_id" {}
variable "region" {}
variable "tenancy_id" {}

variable "gitops_agent" {}
variable "enable_multicluster" {
  type = bool
}
variable "flux_fleet_member_name" {
  type = string
}
variable "development_overwrite_repositories" {
  type = bool
}

# NOTIFICATION
variable "create_notification_topic" {
  type = bool
}
variable "notification_topic_id" {}
variable "notification_topic_name" {}
variable "notification_topic_description" {}

# PROJECT
variable "devops_project_name" {}
variable "devops_project_description" {}

# DEVOPS PROJECT LOG GROUP
variable "devops_log_group_name" {}
variable "devops_log_group_description" {}
variable "devops_log_retention_period_in_days" {
  type = number
}

# SECRETS
variable "git_username" {
  description = "Bootstrap-only OCI DevOps Git username used to seed repositories"
}
variable "git_password" {
  description = "Bootstrap-only OCI DevOps Git password used to seed repositories"
  sensitive   = true
}

# TEMPLATE
variable "ocir_repo_path_prefix" {}

# OKE ENVIRONMENT
variable "oke_cluster_id" {}
variable "oke_environment_name" {}
variable "oke_environment_description" {}
variable "oke_worker_subnet_id" {}
variable "oke_worker_nsg_id" {}
