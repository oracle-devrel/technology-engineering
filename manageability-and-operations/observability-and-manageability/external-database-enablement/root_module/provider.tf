terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.11.0"
    }
  }
}

provider "oci" {
  # Configuration options
  tenancy_ocid     = "ocid1.tenancy.oc1..XXXXXX"
  user_ocid        = "ocid1.user.oc1..XXXXXX"
  private_key_path = "/path/private_key.pem"
  fingerprint      = ""
  region           = ""
}