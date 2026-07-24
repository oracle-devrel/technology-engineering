terraform {
  required_version = ">= 1.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0"
    }
  }
}

# ORM injects authentication automatically — no API key config needed.
provider "oci" {
  tenancy_ocid = var.tenancy_ocid
  region       = var.region
}
