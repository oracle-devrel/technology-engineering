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

variable "applications" {
  description = "Application objects with globally unique components. Legacy JSON strings remain accepted."
  # Accept native RM complex inputs without breaking existing JSON-string stacks.
  type = any
  default = [{
    name       = "sample-app"
    components = [{ name = "sample-api" }, { name = "sample-worker" }]
  }]

  validation {
    condition = can([
      for application in try(jsondecode(var.applications), var.applications) : {
        name = application.name
        components = [
          for component in application.components : component.name
        ]
      }
    ])
    error_message = "applications must be a JSON array whose entries contain name and a components array with component names."
  }

  validation {
    condition     = can(length(try(jsondecode(var.applications), var.applications)) > 0) ? length(try(jsondecode(var.applications), var.applications)) > 0 : true
    error_message = "applications must contain at least one application."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : concat(
        [can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", application.name)) && length(application.name) <= 46],
        [for component in application.components : can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", component.name)) && length(component.name) <= 45]
      )
      ]))) ? alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : concat(
        [can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", application.name)) && length(application.name) <= 46],
        [for component in application.components : can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", component.name)) && length(component.name) <= 45]
      )
    ])) : true
    error_message = "Application and component names must be Kubernetes DNS labels. Applications are limited to 46 characters and components to 45 so derived Helm release names remain valid."
  }

  validation {
    condition = can([for application in try(jsondecode(var.applications), var.applications) : application.name]) ? length(distinct([
      for application in try(jsondecode(var.applications), var.applications) : application.name
    ])) == length(try(jsondecode(var.applications), var.applications)) : true
    error_message = "Application names must be unique."
  }

  validation {
    condition = can(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components : component.name
      ]
      ])) ? length(distinct(flatten([
        for application in try(jsondecode(var.applications), var.applications) : [
          for component in application.components : component.name
        ]
      ]))) == length(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components : component.name
      ]
    ])) : true
    error_message = "Component names must be globally unique across all applications."
  }

  validation {
    condition = can(alltrue([
      for application in try(jsondecode(var.applications), var.applications) : length(application.components) > 0
      ])) ? alltrue([
      for application in try(jsondecode(var.applications), var.applications) : length(application.components) > 0
    ]) : true
    error_message = "Every application must contain at least one component."
  }

  validation {
    condition = can(alltrue([
      for application in try(jsondecode(var.applications), var.applications) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(application.namespace, null), application.name))) &&
      length(coalesce(try(application.namespace, null), application.name)) <= 63 &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(application.prod_namespace, null), coalesce(try(application.namespace, null), application.name)))) &&
      length(coalesce(try(application.prod_namespace, null), coalesce(try(application.namespace, null), application.name))) <= 63
      ])) ? alltrue([
      for application in try(jsondecode(var.applications), var.applications) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(application.namespace, null), application.name))) &&
      length(coalesce(try(application.namespace, null), application.name)) <= 63 &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", coalesce(try(application.prod_namespace, null), coalesce(try(application.namespace, null), application.name)))) &&
      length(coalesce(try(application.prod_namespace, null), coalesce(try(application.namespace, null), application.name))) <= 63
    ]) : true
    error_message = "Application noprod and prod namespaces must be Kubernetes DNS labels of at most 63 characters."
  }

  validation {
    condition = can(try(jsondecode(var.applications), var.applications)) ? (
      length(distinct([
        for application in try(jsondecode(var.applications), var.applications) : coalesce(try(application.namespace, null), application.name)
      ])) == length(try(jsondecode(var.applications), var.applications)) &&
      length(distinct([
        for application in try(jsondecode(var.applications), var.applications) : coalesce(try(application.prod_namespace, null), coalesce(try(application.namespace, null), application.name))
      ])) == length(try(jsondecode(var.applications), var.applications))
    ) : true
    error_message = "Application namespaces must be unique within both the noprod and prod clusters."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : concat(
        [
          can(regex("^[a-z0-9][a-z0-9._-]*[a-z0-9]$|^[a-z0-9]$", coalesce(try(application.chart_repository_name, null), "${application.name}-chart"))) &&
          length(coalesce(try(application.chart_repository_name, null), "${application.name}-chart")) <= 100 &&
          can(regex("^[a-z0-9][a-z0-9._/-]*[a-z0-9]$|^[a-z0-9]$", coalesce(try(application.chart_path, null), application.name))) &&
          !startswith(coalesce(try(application.chart_path, null), application.name), "/") &&
          !strcontains(coalesce(try(application.chart_path, null), application.name), "..") &&
          length(coalesce(try(application.chart_path, null), application.name)) <= 120 &&
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", coalesce(try(application.chart_version, null), "0.1.0")))
        ],
        [
          for component in application.components :
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", coalesce(try(component.chart_version, null), "0.1.0")))
        ]
      )
      ]))) ? alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : concat(
        [
          can(regex("^[a-z0-9][a-z0-9._-]*[a-z0-9]$|^[a-z0-9]$", coalesce(try(application.chart_repository_name, null), "${application.name}-chart"))) &&
          length(coalesce(try(application.chart_repository_name, null), "${application.name}-chart")) <= 100 &&
          can(regex("^[a-z0-9][a-z0-9._/-]*[a-z0-9]$|^[a-z0-9]$", coalesce(try(application.chart_path, null), application.name))) &&
          !startswith(coalesce(try(application.chart_path, null), application.name), "/") &&
          !strcontains(coalesce(try(application.chart_path, null), application.name), "..") &&
          length(coalesce(try(application.chart_path, null), application.name)) <= 120 &&
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", coalesce(try(application.chart_version, null), "0.1.0")))
        ],
        [
          for component in application.components :
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", coalesce(try(component.chart_version, null), "0.1.0")))
        ]
      )
    ])) : true
    error_message = "Chart repository names and paths must use safe lowercase relative naming within their length limits, and chart versions must use SemVer."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components :
        can(regex("^[A-Za-z0-9._/-]+[.]ya?ml$", coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"))) &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "/") &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "script/") &&
        !strcontains(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "..") &&
        length(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml")) <= 255
      ]
      ]))) ? alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components :
        can(regex("^[A-Za-z0-9._/-]+[.]ya?ml$", coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"))) &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "/") &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "script/") &&
        !strcontains(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "..") &&
        length(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml")) <= 255
      ]
    ])) : true
    error_message = "Component build_spec_path values must be safe relative .yaml or .yml paths outside the managed script directory."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components :
        !contains(concat(
          ["README.md", "helm-chart-pipeline.yaml"],
          [for configured_application in try(jsondecode(var.applications), var.applications) : "${configured_application.name}-package-pipeline.yaml"],
          flatten([for configured_application in try(jsondecode(var.applications), var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-release-pipeline.yaml"]]),
          flatten([for configured_application in try(jsondecode(var.applications), var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-build-pipeline.yaml" if try(configured_component.build_spec_path, null) == null]])
        ), component.build_spec_path) if try(trimspace(component.build_spec_path), "") != ""
      ]
      ]))) ? alltrue(flatten([
      for application in try(jsondecode(var.applications), var.applications) : [
        for component in application.components :
        !contains(concat(
          ["README.md", "helm-chart-pipeline.yaml"],
          [for configured_application in try(jsondecode(var.applications), var.applications) : "${configured_application.name}-package-pipeline.yaml"],
          flatten([for configured_application in try(jsondecode(var.applications), var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-release-pipeline.yaml"]]),
          flatten([for configured_application in try(jsondecode(var.applications), var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-build-pipeline.yaml" if try(configured_component.build_spec_path, null) == null]])
        ), component.build_spec_path) if try(trimspace(component.build_spec_path), "") != ""
      ]
    ])) : true
    error_message = "Explicit component build_spec_path values cannot collide with stack-managed pipeline repository files."
  }
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
