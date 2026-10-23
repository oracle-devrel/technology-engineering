variable "customize_environment_names" {
  description = "Show environment and cluster target naming inputs in Resource Manager."
  type        = bool
  default     = false
}

variable "dev_environment_name" {
  type        = string
  default     = "dev"
  nullable    = false
  description = "Name of the development application environment."
}

variable "staging_environment_name" {
  type        = string
  default     = "staging"
  nullable    = false
  description = "Name of the release-candidate application environment."
}

variable "prod_environment_name" {
  type        = string
  default     = "prod"
  nullable    = false
  description = "Name of the approved production application environment."
}

variable "noprod_cluster_name" {
  type        = string
  default     = "noprod"
  nullable    = false
  description = "Name of the nonproduction cluster target, not the OKE cluster itself."
}

variable "prod_cluster_name" {
  type        = string
  default     = "prod"
  nullable    = false
  description = "Name of the approved production cluster target, not the OKE cluster itself."
}

locals {
  environment_names = {
    dev            = var.dev_environment_name
    staging        = var.staging_environment_name
    prod           = var.prod_environment_name
    noprod_cluster = var.noprod_cluster_name
    prod_cluster   = var.prod_cluster_name
  }

  # Include cluster and namespace so shared-cluster installs are checked too.
  application_release_identities = flatten([
    for application in local.application_config : concat(
      [jsonencode([var.oke_cluster_id, coalesce(try(application.namespace, null), application.name), "${application.name}-${var.noprod_cluster_name}"])],
      [jsonencode([var.prod_oke_cluster_id, coalesce(try(application.prod_namespace, null), try(application.namespace, null), application.name), application.name])],
      flatten([for component in application.components : [
        jsonencode([var.oke_cluster_id, coalesce(try(application.namespace, null), application.name), "${component.name}-${var.dev_environment_name}"]),
        jsonencode([var.oke_cluster_id, coalesce(try(application.namespace, null), application.name), "${component.name}-${var.staging_environment_name}"]),
        jsonencode([var.prod_oke_cluster_id, coalesce(try(application.prod_namespace, null), try(application.namespace, null), application.name), component.name])
      ]])
    )
  ])
}

resource "terraform_data" "environment_names" {
  input = local.environment_names

  lifecycle {
    precondition {
      condition = alltrue([
        for name in values(local.environment_names) :
        length(name) <= 63 && can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", name))
      ])
      error_message = "Environment and cluster target names must be lowercase Kubernetes DNS labels of at most 63 characters."
    }
    precondition {
      condition     = length(distinct([var.dev_environment_name, var.staging_environment_name, var.prod_environment_name])) == 3
      error_message = "Development, staging and production application environment names must be distinct."
    }
    precondition {
      condition     = var.noprod_cluster_name != var.prod_cluster_name
      error_message = "Nonproduction and production cluster target names must be distinct."
    }
    precondition {
      condition     = !local.application_delivery_enabled || length(distinct(local.application_release_identities)) == length(local.application_release_identities)
      error_message = "Generated Helm release names collide in the same cluster and namespace. Choose different application, component or environment names."
    }
    precondition {
      condition = !local.application_delivery_enabled || alltrue(flatten([
        for application in local.application_config : concat(
          [length("${application.name}-${var.noprod_cluster_name}") <= 53, length(application.name) <= 53],
          [for component in application.components : alltrue([
            length("${component.name}-${var.dev_environment_name}") <= 53,
            length("${component.name}-${var.staging_environment_name}") <= 53,
            length(component.name) <= 53
          ])]
        )
      ]))
      error_message = "Generated application and component Helm release names must not exceed 53 characters; shorten the entity or environment name."
    }
  }
}

output "environment_names" {
  description = "Configured application environment and cluster target names, keyed by stable workflow role."
  value       = local.environment_names
}
