variable "region" {}
variable "tenancy_ocid" {}
variable "current_user_ocid" {}
variable "compartment_ocid" {}


variable "gitops_agent" {
  default = "argocd"
}

variable "gitops_scope" {
  description = "Initial GitOps repository scope: cluster administration only, or cluster administration plus developer application placements"
  type        = string
  default     = "cluster_admin"

  validation {
    condition     = contains(["cluster_admin", "applications_and_cluster"], var.gitops_scope)
    error_message = "gitops_scope must be cluster_admin or applications_and_cluster."
  }
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

# Maintainer switch, explicitly hidden in the Resource Manager schema.
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
variable "create_devops_project" {
  description = "Create a new OCI DevOps project. When false, add the GitOps resources to existing_devops_project_id."
  type        = bool
  default     = true
}

variable "existing_devops_project_id" {
  description = "Existing OCI DevOps project OCID used when create_devops_project is false."
  type        = string
  default     = ""
}

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
variable "pipelines_repository_name" {
  description = "Name of the OCI Code Repository containing GitOps bootstrap and mirror pipelines"
  type        = string
  default     = "gitops-pipelines"

  validation {
    condition     = can(regex("^[A-Za-z0-9_.-]+$", var.pipelines_repository_name)) && length(var.pipelines_repository_name) <= 100
    error_message = "pipelines_repository_name must contain only letters, numbers, periods, underscores, or hyphens and be at most 100 characters."
  }
}

variable "ocir_repo_path_prefix" {
  description = "Base OCIR path for your company and organization; charts add /charts and images use the prefix directly"
  type        = string
  default     = "company-name/org"
}
variable "auth_token" {
  description = "Bootstrap-only auth token used by Resource Manager to seed OCI DevOps repositories; never installed in Kubernetes"
  sensitive   = true
  type        = string
  validation {
    condition     = try(trimspace(var.auth_token) != "", false)
    error_message = "Provide the applying user's auth token for initial repository seeding."
  }
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

variable "iam_policy_compartment_id" {
  description = "Compartment containing the IAM policy; must be an ancestor of every referenced compartment. Null uses the tenancy root."
  type        = string
  default     = null
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

variable "create_automatic_credentials" {
  description = "Create runtime Git and OCIR reader accounts, a Vault, JSON credential secrets and their access policy"
  type        = bool
  default     = false
}

variable "automation_iam_domain_compartment_id" {
  description = "Compartment filtering the automation identity-domain picker"
  type        = string
  default     = null
}

variable "automation_iam_domain_id" {
  description = "Identity domain for generated runtime reader accounts and groups"
  type        = string
  default     = null
}

variable "automatic_credentials_email" {
  description = "Contact address for non-human automation accounts; no activation email is sent"
  type        = string
  default     = "automation@example.com"
}
