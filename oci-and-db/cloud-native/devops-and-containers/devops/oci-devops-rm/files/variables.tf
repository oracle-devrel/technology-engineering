variable "region" {}
variable "tenancy_ocid" {}
variable "current_user_ocid" {}
variable "compartment_ocid" {}

variable "devops_compartment_id" {
  default = null
}

variable "create_devops_project" {
  description = "Create a new OCI DevOps project. When false, generated resources are added to existing_devops_project_id."
  type        = bool
  default     = true
}

variable "existing_devops_project_id" {
  description = "Existing OCI DevOps project OCID used when create_devops_project is false."
  default     = null
}

variable "application_delivery_mode" {
  description = "Application workflow created by this stack: full OCI DevOps delivery or build-only CI for an external deployment system."
  type        = string
  default     = "oci_devops"

  validation {
    condition     = contains(["oci_devops", "build_only"], var.application_delivery_mode)
    error_message = "application_delivery_mode must be either oci_devops or build_only."
  }
}

variable "devops_pipeline_repository_name" {
  description = "Name of the shared OCI DevOps repository containing build specifications and helper scripts."
  type        = string
  default     = "devops-pipelines"

  validation {
    condition = (
      can(regex("^[A-Za-z0-9][A-Za-z0-9._-]*$", var.devops_pipeline_repository_name)) &&
      length(var.devops_pipeline_repository_name) <= 100
    )
    error_message = "devops_pipeline_repository_name must contain 1-100 letters, numbers, periods, underscores, or hyphens and begin with a letter or number."
  }
}

variable "devops_project_name" {
  default = "oke-devops-starter"

  validation {
    condition = (
      trimspace(var.devops_project_name) != "" &&
      replace(lower(var.devops_project_name), "/[^a-z0-9._-]+/", "-") != "" &&
      length(var.devops_project_name) <= 100
    )
    error_message = "devops_project_name must be nonempty, produce a valid image/chart prefix, and contain at most 100 characters."
  }
}

variable "devops_project_description" {
  default = "Beginner-friendly OCI DevOps project for OKE Helm delivery"
}

variable "devops_log_group_name" {
  default = "oke-helm-starter-logs"
}

variable "devops_log_group_description" {
  default = "OCI DevOps logs for the OKE Helm starter project"
}

variable "devops_log_name" {
  default = null
}

variable "devops_log_is_enabled" {
  type    = bool
  default = true
}

variable "devops_log_retention_period_in_days" {
  type    = number
  default = 30
}

variable "create_notification_topic" {
  type    = bool
  default = true
}

variable "notification_topic_id" {
  default = null
}

variable "notification_topic_name" {
  default = "oke-helm-starter-topic"
}

variable "notification_topic_description" {
  default = "OCI DevOps notifications for the OKE Helm starter project"
}

variable "oke_compartment_id" {
  default = null
}

variable "oke_cluster_id" {
  default = null
}

variable "prod_oke_cluster_id" {
  default = null
}

variable "prod_oke_compartment_id" {
  default = null
}

variable "network_compartment_id" {
  default = null
}

variable "prod_network_compartment_id" {
  default = null
}

variable "oke_vcn_id" {
  default = null
}

variable "prod_oke_vcn_id" {
  default = null
}

variable "oke_worker_subnet_id" {
  default = null
}

variable "oke_worker_nsg_id" {
  default = null
}

variable "prod_oke_worker_subnet_id" {
  default = null
}

variable "prod_oke_worker_nsg_id" {
  default = null
}

variable "enable_cluster_admin" {
  description = "Create the optional OCI DevOps cluster-administration workflow."
  type        = bool
  default     = false
}

variable "cluster_admin_artifact_repository_name" {
  description = "Optional display name for the Generic Artifact repository containing cluster-admin values and production plans. Empty derives the name from the DevOps project."
  type        = string
  default     = ""

  validation {
    condition = trimspace(var.cluster_admin_artifact_repository_name) == "" || (
      var.cluster_admin_artifact_repository_name == trimspace(var.cluster_admin_artifact_repository_name) &&
      length(var.cluster_admin_artifact_repository_name) <= 255 &&
      can(regex("^[A-Za-z0-9][A-Za-z0-9._ -]*$", var.cluster_admin_artifact_repository_name))
    )
    error_message = "cluster_admin_artifact_repository_name must be empty or a 1-255 character name beginning with a letter or number and containing only letters, numbers, spaces, periods, underscores, and hyphens."
  }
}

variable "cluster_administration" {
  description = "Shared Kubernetes tool topology with pinned chart sources. Legacy JSON strings remain accepted."
  type        = any
  default = [
    { name = "keda", repository = "https://kedacore.github.io/charts", chart = "keda", version = "2.20.1", namespace = "keda", depends_on = [] },
    { name = "kube-prometheus", repository = "https://prometheus-community.github.io/helm-charts", chart = "kube-prometheus-stack", version = "87.10.1", namespace = "monitoring", depends_on = [] }
  ]

  validation {
    condition = can([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : {
        name       = tool.name
        repository = tool.repository
        chart      = tool.chart
        version    = tool.version
        namespace  = coalesce(try(tool.namespace, null), tool.name)
        depends_on = compact(coalesce(try(tool.depends_on, null), []))
      }
    ])
    error_message = "cluster_administration must contain a tools array whose entries define name, repository, chart, and version. Legacy input with noprod.tools is also accepted."
  }

  validation {
    condition = can(alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      can(regex("^(https|oci)://[^[:space:]]+$", tool.repository)) &&
      can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", tool.chart)) &&
      can(regex("^[0-9A-Za-z][0-9A-Za-z._+-]*$", tool.version))
      ])) ? alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      can(regex("^(https|oci)://[^[:space:]]+$", tool.repository)) &&
      can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", tool.chart)) &&
      can(regex("^[0-9A-Za-z][0-9A-Za-z._+-]*$", tool.version))
    ]) : true
    error_message = "Each cluster tool must define an HTTPS Helm repository or OCI chart repository, a valid chart name, and a pinned chart version."
  }

  validation {
    condition = can(alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", tool.name)) &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(tool.namespace, null), tool.name))) &&
      length(tool.name) <= 63 && length(coalesce(try(tool.namespace, null), tool.name)) <= 63
      ])) ? alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", tool.name)) &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(tool.namespace, null), tool.name))) &&
      length(tool.name) <= 63 && length(coalesce(try(tool.namespace, null), tool.name)) <= 63
    ]) : true
    error_message = "Cluster tool names and namespaces must be valid Kubernetes DNS labels of at most 63 characters."
  }

  validation {
    condition = can(
      length(distinct([for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : tool.name])) ==
      length(try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)))
      ) ? (
      length(distinct([for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : tool.name])) ==
      length(try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)))
    ) : true
    error_message = "Tool names must be unique."
  }

  validation {
    condition = can(
      length(distinct([
        for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : coalesce(try(tool.namespace, null), tool.name)
        ])) == length([
        for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : coalesce(try(tool.namespace, null), tool.name)
      ])
      ) ? (
      length(distinct([
        for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : coalesce(try(tool.namespace, null), tool.name)
        ])) == length([
        for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : coalesce(try(tool.namespace, null), tool.name)
      ])
    ) : true
    error_message = "Each tool must use a unique namespace."
  }

  validation {
    condition = can(alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      alltrue([
        for dependency in compact(coalesce(try(tool.depends_on, null), [])) :
        dependency != tool.name && contains(
          [for candidate in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : candidate.name],
          dependency
        )
      ]) && length(distinct(compact(coalesce(try(tool.depends_on, null), [])))) == length(compact(coalesce(try(tool.depends_on, null), [])))
      ])) ? alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      alltrue([
        for dependency in compact(coalesce(try(tool.depends_on, null), [])) :
        dependency != tool.name && contains(
          [for candidate in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) : candidate.name],
          dependency
        )
      ]) && length(distinct(compact(coalesce(try(tool.depends_on, null), [])))) == length(compact(coalesce(try(tool.depends_on, null), [])))
    ]) : true
    error_message = "Tool dependencies must be unique, reference another configured tool, and cannot reference the tool itself."
  }

  validation {
    condition = try(alltrue([
      for tool in try(try(jsondecode(var.cluster_administration), var.cluster_administration).tools, try(jsondecode(var.cluster_administration), var.cluster_administration).noprod.tools, try(jsondecode(var.cluster_administration), var.cluster_administration)) :
      (try(tool.mirror_images, null) == null || try(tool.mirror_images, null) == true || try(tool.mirror_images, null) == false) &&
      can(concat(coalesce(try(tool.additional_images, null), []), [])) && alltrue([
        for image in coalesce(try(tool.additional_images, null), []) :
        image == tostring(image) && can(regex("^[A-Za-z0-9][A-Za-z0-9._/@:+-]*$", image)) && !strcontains(image, "://")
        if image != ""
      ])
    ]), false)
    error_message = "Tool mirror_images must be a boolean; additional_images must be a list of container image references without URLs, credentials or whitespace."
  }
}

variable "namespace_init_secret_name" {
  default = "ocirsecret"

  validation {
    condition     = can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", var.namespace_init_secret_name)) && length(var.namespace_init_secret_name) <= 63
    error_message = "namespace_init_secret_name must be a Kubernetes DNS label of at most 63 characters."
  }
}

variable "namespace_init_secret_compartment_id" {
  description = "Deprecated compatibility input; bootstrap credentials use the DevOps project compartment."
  default     = null
}

variable "auth_token" {
  type      = string
  default   = null
  sensitive = true
}

variable "create_automatic_credentials" {
  type        = bool
  default     = false
  description = "Create automation users, auth tokens, a Vault, an AES key, credential secrets and their access policy. Pipeline execution IAM remains controlled by create_iam."
}

variable "automatic_credentials_compartment_id" {
  type        = string
  default     = null
  description = "Deprecated compatibility input; generated Vault, key and secrets always use the resolved DevOps project compartment."
  validation {
    condition     = var.automatic_credentials_compartment_id == null ? true : can(regex("^ocid1\\.compartment\\.", var.automatic_credentials_compartment_id))
    error_message = "Use a compartment OCID."
  }
}

variable "automatic_credentials_email" {
  type        = string
  default     = "automation@example.com"
  description = "Contact email for the generated service accounts, required by identity domains."
  validation {
    condition     = var.automatic_credentials_email == "" || can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.automatic_credentials_email))
    error_message = "Use a valid contact email address."
  }
}

variable "iam_policy_compartment_id" {
  type        = string
  default     = null
  description = "Common ancestor of the DevOps, OKE, and network compartments for policy attachment. Defaults to the tenancy root; grants remain scoped to their selected compartments."
  validation {
    condition     = var.iam_policy_compartment_id == null ? true : can(regex("^ocid1\\.(compartment|tenancy)\\.", var.iam_policy_compartment_id))
    error_message = "Use a compartment or tenancy OCID."
  }
}

variable "create_iam" {
  type    = bool
  default = false
}

variable "iam_domain_compartment_id" {
  default = null
}

variable "pipeline_iam_domain_compartment_id" {
  type        = string
  default     = null
  description = "Compartment containing the identity domain selected for the pipeline dynamic group."
}

variable "pipeline_iam_domain_id" {
  type        = string
  default     = null
  description = "Identity domain for the pipeline dynamic group. Legacy stacks fall back to devops_iam_domain_id when omitted."
}

variable "devops_iam_domain_id" {
  default = null
}

variable "devops_dynamic_group_name" {
  default = "OkeHelmStarterDevOpsDynamicGroup"
}

variable "devops_policy_name" {
  default = "oke-helm-starter-devops-policy"
}

variable "development_mode" {
  description = "Internal mode used by development archives to refresh template-owned repository files."
  type        = bool
  default     = false
}
