variable "compartment_id" {}
variable "region" {}
variable "tenancy_id" {}
variable "git_username" {}
variable "git_password" {
  sensitive = true
}

variable "create_notification_topic" {
  type = bool
}
variable "notification_topic_id" {}
variable "notification_topic_name" {}
variable "notification_topic_description" {}

variable "devops_project_name" {}
variable "devops_project_description" {}
variable "devops_log_group_name" {}
variable "devops_log_group_description" {}
variable "devops_log_name" {}
variable "devops_log_is_enabled" {
  type = bool
}
variable "devops_log_retention_period_in_days" {
  type = number
}

variable "oke_cluster_id" {}
variable "oke_worker_subnet_id" {}
variable "oke_worker_nsg_id" {}
variable "prod_oke_cluster_id" {
  default = null
}
variable "prod_oke_compartment_id" {
  default = null
}
variable "prod_oke_worker_subnet_id" {
  default = null
}
variable "prod_oke_worker_nsg_id" {
  default = null
}
variable "namespace_init_secret_name" {}

variable "applications" {
  type = list(object({
    name                  = string
    chart_repository_name = optional(string)
    chart_path            = optional(string)
    chart_version         = optional(string, "0.1.0")
    namespace             = optional(string)
    prod_namespace        = optional(string)
    kubernetes_group      = optional(string, "")
    components = list(object({
      name            = string
      chart_version   = optional(string, "0.1.0")
      build_spec_path = optional(string)
    }))
  }))
}

variable "enable_cluster_admin" {
  type    = bool
  default = false
}

variable "cluster_admin_artifact_repository_name" {
  type    = string
  default = ""
}

variable "cluster_administration" {
  type = object({
    tools = optional(list(object({
      name       = string
      repository = string
      chart      = string
      version    = string
      namespace  = optional(string)
      depends_on = optional(list(string), [])
    })))
    noprod = optional(object({
      approval_required = optional(bool, false)
      tools = optional(list(object({
        name       = string
        repository = string
        chart      = string
        version    = string
        namespace  = optional(string)
        depends_on = optional(list(string), [])
      })))
    }))
    prod = optional(object({
      approval_required = optional(bool, true)
      tools = optional(list(object({
        name       = string
        repository = string
        chart      = string
        version    = string
        namespace  = optional(string)
        depends_on = optional(list(string), [])
      })))
    }))
  })
}

variable "development_mode" {
  type    = bool
  default = false
}
