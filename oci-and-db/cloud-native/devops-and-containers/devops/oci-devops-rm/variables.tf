variable "region" {}
variable "tenancy_ocid" {}
variable "current_user_ocid" {}
variable "compartment_ocid" {}

variable "devops_compartment_id" {
  default = null
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

variable "oke_cluster_id" {}

variable "prod_oke_cluster_id" {
  default = null

  validation {
    condition     = try(trimspace(var.prod_oke_cluster_id), "") != ""
    error_message = "prod_oke_cluster_id is required for the production OKE environment."
  }
}

variable "prod_oke_compartment_id" {
  default = null

  validation {
    condition     = try(trimspace(var.prod_oke_compartment_id), "") != ""
    error_message = "prod_oke_compartment_id is required for the production OKE cluster."
  }
}

variable "network_compartment_id" {
  default = null
}

variable "prod_network_compartment_id" {
  default = null

  validation {
    condition     = try(trimspace(var.prod_network_compartment_id), "") != ""
    error_message = "prod_network_compartment_id is required for the production OKE network configuration."
  }
}

variable "oke_vcn_id" {
  default = null
}

variable "prod_oke_vcn_id" {
  default = null

  validation {
    condition     = try(trimspace(var.prod_oke_vcn_id), "") != ""
    error_message = "prod_oke_vcn_id is required for the production OKE network configuration."
  }
}

variable "oke_worker_subnet_id" {
  default = null

  validation {
    condition     = try(trimspace(var.oke_worker_subnet_id), "") != ""
    error_message = "oke_worker_subnet_id is required for application bootstrap shell stage execution."
  }
}

variable "oke_worker_nsg_id" {
  default = null
}

variable "prod_oke_worker_subnet_id" {
  default = null

  validation {
    condition     = try(trimspace(var.prod_oke_worker_subnet_id), "") != ""
    error_message = "prod_oke_worker_subnet_id is required for production private endpoint and shell stage execution."
  }
}

variable "prod_oke_worker_nsg_id" {
  default = null
}

variable "applications" {
  description = "JSON array of applications and globally unique components to bootstrap in OCI DevOps."
  type        = string
  default     = <<-JSON
  [
    {
      "name": "sample-app",
      "components": [
        {
          "name": "sample-api"
        },
        {
          "name": "sample-worker"
        }
      ]
    }
  ]
  JSON

  validation {
    condition = can([
      for application in jsondecode(var.applications) : {
        name = application.name
        components = [
          for component in application.components : component.name
        ]
      }
    ])
    error_message = "applications must be a JSON array whose entries contain name and a components array with component names."
  }

  validation {
    condition     = can(length(jsondecode(var.applications)) > 0) ? length(jsondecode(var.applications)) > 0 : true
    error_message = "applications must contain at least one application."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in jsondecode(var.applications) : concat(
        [can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", application.name)) && length(application.name) <= 46],
        [for component in application.components : can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", component.name)) && length(component.name) <= 45]
      )
      ]))) ? alltrue(flatten([
      for application in jsondecode(var.applications) : concat(
        [can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", application.name)) && length(application.name) <= 46],
        [for component in application.components : can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", component.name)) && length(component.name) <= 45]
      )
    ])) : true
    error_message = "Application and component names must be Kubernetes DNS labels. Applications are limited to 46 characters and components to 45 so derived Helm release names remain valid."
  }

  validation {
    condition = can([for application in jsondecode(var.applications) : application.name]) ? length(distinct([
      for application in jsondecode(var.applications) : application.name
    ])) == length(jsondecode(var.applications)) : true
    error_message = "Application names must be unique."
  }

  validation {
    condition = can(flatten([
      for application in jsondecode(var.applications) : [
        for component in application.components : component.name
      ]
      ])) ? length(distinct(flatten([
        for application in jsondecode(var.applications) : [
          for component in application.components : component.name
        ]
      ]))) == length(flatten([
      for application in jsondecode(var.applications) : [
        for component in application.components : component.name
      ]
    ])) : true
    error_message = "Component names must be globally unique across all applications."
  }

  validation {
    condition = can(alltrue([
      for application in jsondecode(var.applications) : length(application.components) > 0
      ])) ? alltrue([
      for application in jsondecode(var.applications) : length(application.components) > 0
    ]) : true
    error_message = "Every application must contain at least one component."
  }

  validation {
    condition = can(alltrue([
      for application in jsondecode(var.applications) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(application.namespace, application.name))) &&
      length(try(application.namespace, application.name)) <= 63 &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(application.prod_namespace, try(application.namespace, application.name)))) &&
      length(try(application.prod_namespace, try(application.namespace, application.name))) <= 63
      ])) ? alltrue([
      for application in jsondecode(var.applications) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(application.namespace, application.name))) &&
      length(try(application.namespace, application.name)) <= 63 &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(application.prod_namespace, try(application.namespace, application.name)))) &&
      length(try(application.prod_namespace, try(application.namespace, application.name))) <= 63
    ]) : true
    error_message = "Application noprod and prod namespaces must be Kubernetes DNS labels of at most 63 characters."
  }

  validation {
    condition = can(jsondecode(var.applications)) ? (
      length(distinct([
        for application in jsondecode(var.applications) : try(application.namespace, application.name)
      ])) == length(jsondecode(var.applications)) &&
      length(distinct([
        for application in jsondecode(var.applications) : try(application.prod_namespace, try(application.namespace, application.name))
      ])) == length(jsondecode(var.applications))
    ) : true
    error_message = "Application namespaces must be unique within both the noprod and prod clusters."
  }

  validation {
    condition = can(jsondecode(var.applications)) ? length(distinct(concat(
      ["pipelines", "cluster-admin"],
      [for application in jsondecode(var.applications) : try(application.chart_repository_name, "${application.name}-chart")],
      flatten([for application in jsondecode(var.applications) : [for component in application.components : component.name]])
      ))) == length(concat(
      ["pipelines", "cluster-admin"],
      [for application in jsondecode(var.applications) : try(application.chart_repository_name, "${application.name}-chart")],
      flatten([for application in jsondecode(var.applications) : [for component in application.components : component.name]])
    )) : true
    error_message = "Derived repository names must be unique and cannot collide with the reserved pipelines or cluster-admin repositories."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in jsondecode(var.applications) : concat(
        [
          can(regex("^[a-z0-9][a-z0-9._-]*[a-z0-9]$|^[a-z0-9]$", try(application.chart_repository_name, "${application.name}-chart"))) &&
          length(try(application.chart_repository_name, "${application.name}-chart")) <= 100 &&
          can(regex("^[a-z0-9][a-z0-9._/-]*[a-z0-9]$|^[a-z0-9]$", try(application.chart_path, application.name))) &&
          !startswith(try(application.chart_path, application.name), "/") &&
          !strcontains(try(application.chart_path, application.name), "..") &&
          length(try(application.chart_path, application.name)) <= 120 &&
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", try(application.chart_version, "0.1.0")))
        ],
        [
          for component in application.components :
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", try(component.chart_version, "0.1.0")))
        ]
      )
      ]))) ? alltrue(flatten([
      for application in jsondecode(var.applications) : concat(
        [
          can(regex("^[a-z0-9][a-z0-9._-]*[a-z0-9]$|^[a-z0-9]$", try(application.chart_repository_name, "${application.name}-chart"))) &&
          length(try(application.chart_repository_name, "${application.name}-chart")) <= 100 &&
          can(regex("^[a-z0-9][a-z0-9._/-]*[a-z0-9]$|^[a-z0-9]$", try(application.chart_path, application.name))) &&
          !startswith(try(application.chart_path, application.name), "/") &&
          !strcontains(try(application.chart_path, application.name), "..") &&
          length(try(application.chart_path, application.name)) <= 120 &&
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", try(application.chart_version, "0.1.0")))
        ],
        [
          for component in application.components :
          can(regex("^[0-9]+\\.[0-9]+\\.[0-9]+([-+][0-9A-Za-z.-]+)?$", try(component.chart_version, "0.1.0")))
        ]
      )
    ])) : true
    error_message = "Chart repository names and paths must use safe lowercase relative naming within their length limits, and chart versions must use SemVer."
  }

  validation {
    condition = can(alltrue(flatten([
      for application in jsondecode(var.applications) : [
        for component in application.components :
        can(regex("^[A-Za-z0-9._/-]+[.]ya?ml$", coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"))) &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "/") &&
        !startswith(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "script/") &&
        !strcontains(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml"), "..") &&
        length(coalesce(try(component.build_spec_path, null), "${component.name}-build-pipeline.yaml")) <= 255
      ]
      ]))) ? alltrue(flatten([
      for application in jsondecode(var.applications) : [
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
      for application in jsondecode(var.applications) : [
        for component in application.components :
        !contains(concat(
          ["README.md", "helm-chart-pipeline.yaml"],
          [for configured_application in jsondecode(var.applications) : "${configured_application.name}-package-pipeline.yaml"],
          flatten([for configured_application in jsondecode(var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-release-pipeline.yaml"]]),
          flatten([for configured_application in jsondecode(var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-build-pipeline.yaml" if try(configured_component.build_spec_path, null) == null]])
        ), component.build_spec_path) if try(component.build_spec_path, null) != null
      ]
      ]))) ? alltrue(flatten([
      for application in jsondecode(var.applications) : [
        for component in application.components :
        !contains(concat(
          ["README.md", "helm-chart-pipeline.yaml"],
          [for configured_application in jsondecode(var.applications) : "${configured_application.name}-package-pipeline.yaml"],
          flatten([for configured_application in jsondecode(var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-release-pipeline.yaml"]]),
          flatten([for configured_application in jsondecode(var.applications) : [for configured_component in configured_application.components : "${configured_component.name}-build-pipeline.yaml" if try(configured_component.build_spec_path, null) == null]])
        ), component.build_spec_path) if try(component.build_spec_path, null) != null
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
  description = "JSON object configuring one shared Kubernetes tool topology and its pinned public Helm chart sources for the existing noprod and prod OKE clusters."
  type        = string
  default     = <<-JSON
  {
    "tools": [
      {
        "name": "keda",
        "repository": "https://kedacore.github.io/charts",
        "chart": "keda",
        "version": "2.20.1",
        "namespace": "keda",
        "depends_on": []
      },
      {
        "name": "kube-prometheus",
        "repository": "https://prometheus-community.github.io/helm-charts",
        "chart": "kube-prometheus-stack",
        "version": "87.10.1",
        "namespace": "monitoring",
        "depends_on": []
      }
    ]
  }
  JSON

  validation {
    condition = can([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : {
        name       = tool.name
        repository = tool.repository
        chart      = tool.chart
        version    = tool.version
        namespace  = try(tool.namespace, tool.name)
        depends_on = try(tool.depends_on, [])
      }
    ])
    error_message = "cluster_administration must contain a tools array whose entries define name, repository, chart, and version. Legacy input with noprod.tools is also accepted."
  }

  validation {
    condition = can(alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      can(regex("^(https|oci)://[^[:space:]]+$", tool.repository)) &&
      can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", tool.chart)) &&
      can(regex("^[0-9A-Za-z][0-9A-Za-z._+-]*$", tool.version))
      ])) ? alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      can(regex("^(https|oci)://[^[:space:]]+$", tool.repository)) &&
      can(regex("^[A-Za-z0-9][A-Za-z0-9._/-]*$", tool.chart)) &&
      can(regex("^[0-9A-Za-z][0-9A-Za-z._+-]*$", tool.version))
    ]) : true
    error_message = "Each cluster tool must define an HTTPS Helm repository or OCI chart repository, a valid chart name, and a pinned chart version."
  }

  validation {
    condition = can(alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", tool.name)) &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(tool.namespace, tool.name))) &&
      length(tool.name) <= 63 && length(try(tool.namespace, tool.name)) <= 63
      ])) ? alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", tool.name)) &&
      can(regex("^[a-z0-9]([-a-z0-9]*[a-z0-9])?$", try(tool.namespace, tool.name))) &&
      length(tool.name) <= 63 && length(try(tool.namespace, tool.name)) <= 63
    ]) : true
    error_message = "Cluster tool names and namespaces must be valid Kubernetes DNS labels of at most 63 characters."
  }

  validation {
    condition = can(
      length(distinct([for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : tool.name])) ==
      length(try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools))
      ) ? (
      length(distinct([for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : tool.name])) ==
      length(try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools))
    ) : true
    error_message = "Tool names must be unique."
  }

  validation {
    condition = can(
      length(distinct([
        for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : try(tool.namespace, tool.name)
        ])) == length([
        for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : try(tool.namespace, tool.name)
      ])
      ) ? (
      length(distinct([
        for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : try(tool.namespace, tool.name)
        ])) == length([
        for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : try(tool.namespace, tool.name)
      ])
    ) : true
    error_message = "Each tool must use a unique namespace."
  }

  validation {
    condition = can(alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      alltrue([
        for dependency in try(tool.depends_on, []) :
        dependency != tool.name && contains(
          [for candidate in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : candidate.name],
          dependency
        )
      ]) && length(distinct(try(tool.depends_on, []))) == length(try(tool.depends_on, []))
      ])) ? alltrue([
      for tool in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) :
      alltrue([
        for dependency in try(tool.depends_on, []) :
        dependency != tool.name && contains(
          [for candidate in try(jsondecode(var.cluster_administration).tools, jsondecode(var.cluster_administration).noprod.tools) : candidate.name],
          dependency
        )
      ]) && length(distinct(try(tool.depends_on, []))) == length(try(tool.depends_on, []))
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
  default = null
}

variable "auth_token" {
  sensitive = true
}

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
