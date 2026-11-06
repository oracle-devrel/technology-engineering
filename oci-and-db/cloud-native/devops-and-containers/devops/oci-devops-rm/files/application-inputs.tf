variable "application_definitions" {
  description = "Application names and shared namespace/chart settings."
  type        = any
  default     = [{ name = "sample-app" }]
  nullable    = false

  validation {
    condition = can(concat(try(jsondecode(var.application_definitions), var.application_definitions), [])) && can([
      for application in try(jsondecode(var.application_definitions), var.application_definitions) : application.name
    ])
    error_message = "application_definitions must be a list of application objects with a name."
  }
}

variable "components" {
  description = "Flat components referencing application_definitions by application name."
  type        = any
  default = [
    { application = "sample-app", name = "sample-api" },
    { application = "sample-app", name = "sample-worker" }
  ]
  nullable = false

  validation {
    condition = can(concat(try(jsondecode(var.components), var.components), [])) && can([
      for component in try(jsondecode(var.components), var.components) : {
        name = component.name, application = component.application
      }
    ])
    error_message = "components must be a list of objects with name and application."
  }
}

locals {
  flat_application_definitions = try(jsondecode(var.application_definitions), var.application_definitions)
  flat_components              = try(jsondecode(var.components), var.components)
  grouped_application_config = [for application in local.flat_application_definitions : merge(
    application,
    { components = [for component in local.flat_components : {
      for key, value in component : key => value if key != "application"
    } if component.application == application.name] }
  )]
}

resource "terraform_data" "application_inputs" {
  input = [for application in local.flat_application_definitions : application.name]

  lifecycle {
    precondition {
      condition = alltrue([
        for component in local.flat_components : contains([for application in local.flat_application_definitions : application.name], component.application)
      ])
      error_message = "Every component must reference a configured application name."
    }
    precondition {
      condition     = alltrue([for application in local.flat_application_definitions : !contains(keys(application), "components")])
      error_message = "application_definitions must not contain nested components; use the separate components list."
    }
  }
}

module "application_config" {
  source       = "./modules/application-config"
  applications = local.normalized_application_config
}
