terraform {
  # OCI Resource Manager currently supports the Terraform 1.5.x release line.
  required_version = ">= 1.5.0, < 1.6.0"

  required_providers {
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.5"
    }
    oci = {
      source  = "oracle/oci"
      version = "~> 8.0"
    }
  }
}

provider "oci" {
  region = var.oci_region
}
