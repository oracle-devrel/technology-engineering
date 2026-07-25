terraform {
  required_version = ">=1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "8.1.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.4"
    }
  }
}

provider "oci" {
  ### These information are needed only outside of OCI Terraform Stack Manager
  #tenancy_ocid     = var.tenancy_ocid
  #user_ocid        = var.user_ocid
  #fingerprint      = var.fingerprint
  #private_key_path = var.private_key_path

  ###information needed for ORM
  region           = var.region
}
