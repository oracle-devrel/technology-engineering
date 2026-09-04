terraform {
  required_version = ">=1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "8.19.0"
    }
  }
}

provider "oci" {
  region = var.region
}
