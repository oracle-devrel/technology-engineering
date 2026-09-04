variable "region" {}
variable "tenancy_ocid" {}
variable "current_user_ocid" {}
variable "compartment_ocid" {}


variable "gitops_agent" {
  default = "fluxcd"
}

variable "enable_multicluster" {
  description = "Create fleet-config; Argo CD uses a central hub, while Flux CD activates this stack's selected member and documents manual onboarding for additional clusters"
  type        = bool
  default     = false
}

variable "flux_fleet_member_name" {
  description = "Name of the primary OKE cluster in the decentralized Flux fleet"
  type        = string
  default     = "primary"

  validation {
    condition     = can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", var.flux_fleet_member_name))
    error_message = "flux_fleet_member_name must be a Kubernetes-compatible lowercase name."
  }
}

# Hidden maintainer switch. It is intentionally absent from schema.yaml.
# Customer stacks preserve every Git change after the initial seed. Stack
# developers may set this only in controlled test environments to reset all
# generated repositories to the current local templates on every apply.
variable "development_overwrite_repositories" {
  type        = bool
  default     = false
  description = "DEVELOPMENT ONLY: overwrite generated Git repositories on every apply"
}

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
  type    = number
  default = 30
}

# NOTIFICATION
variable "create_notification_topic" {
  type    = bool
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
  description = "Bootstrap-only auth token used by Resource Manager to seed OCI DevOps repositories; never installed in Kubernetes"
  sensitive   = true
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
variable "oke_worker_subnet_id" {
  description = "Subnet used by the OCI DevOps Container Instance stages that bootstrap the OKE cluster"
  type        = string
}
variable "oke_worker_nsg_id" {
  default = null
}

# IAM
variable "create_iam" {
  type    = bool
  default = false
}

variable "iam_domain_compartment_id" {
  default = null
}

variable "devops_iam_domain_id" {
  default = null
}

variable "devops_dynamic_group_name" {
  default = "DevOpsDynamicGroup"
}

variable "devops_policy_name" {
  default = null
}
variable "kms_compartment_id" {
  default = null
}
