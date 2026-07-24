provider "oci" {}

terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 7.2"
    }
  }
  required_version = ">= 1.0.0 ,<1.6.0"
}

resource "oci_log_analytics_log_analytics_import_custom_content" "import_custom_contents" {
  for_each = var.log_analytics_custom_content_files
  import_custom_content_file = each.value
  namespace                  = var.namespace
  is_overwrite  = true
}

variable "log_analytics_custom_content_files" {
    type = set(any)
    description = "Log Analytics custom content Filepaths"
}

variable "namespace" {
  type = string
  description = "Log Analytics namespace"
}