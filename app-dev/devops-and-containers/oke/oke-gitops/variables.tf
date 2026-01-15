variable "region" {}
variable "tenancy_ocid" {}
variable "current_user_ocid" {}
variable "compartment_ocid" {}

# DEVOPS PROJECT
variable "devops_compartment_id" {}
variable "devops_project_name" {
  default = "oke-gitops"
}
variable "devops_project_description" {
  default = null
}

# DEVOPS LOG GROUP
variable "devops_log_group_name" {
  default = "devops-log-group"
}
variable "devops_log_group_description" {
  default = null
}
variable "devops_log_retention_period_in_days" {
  type = number
  default = 30
}

# NOTIFICATION
variable "create_notification_topic" {
  type = bool
  default = false
}

variable "notification_topic_name" {
  default = "oke-gitops-topic"
}

variable "notification_topic_id" {
  default = null
}

variable "notification_topic_description" {
  default = null
}

# REPOSITORY
variable "ocir_repo_path_prefix" {
  default = "acme/helm"
}
variable "auth_token" {
  sensitive = true
}

# OKE ENVIRONMENT

variable "network_compartment_id" {
  default = null
}
variable "oke_compartment_id" {
  default = null
}

variable "oke_vcn_id" {
  default = null
}

variable "oke_cluster_id" {}
variable "oke_environment_name" {
  default = "oke-cluster"
}
variable "oke_environment_description" {
  default = null
}
variable "is_oke_cluster_private" {
  type = bool
  default = false
}
variable "oke_worker_subnet_id" {
  default = null
}
variable "oke_worker_nsg_id" {
  default = null
}

# IAM
variable "create_iam" {
  type = bool
  default = false
}
variable "devops_policy_name" {
  default = null
}
variable "identity_domain_name" {
  default = "Default"
}
variable "devops_dynamic_group_name" {
  default = "DevOpsDynamicGroup"
}