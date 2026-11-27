variable "applications" {
  description = "JSON array of applications with globally unique components. Native Terraform application objects are also accepted."
  # Preserve native Terraform callers alongside the Resource Manager JSON editor.
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

output "applications" {
  description = "Validated nested applications for either input format."
  value       = var.applications
}
