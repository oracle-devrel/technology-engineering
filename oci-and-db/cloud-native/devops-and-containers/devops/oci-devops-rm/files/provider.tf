terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "2.8.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.4"
    }
    oci = {
      source  = "oracle/oci"
      version = ">= 8.8.0, < 9.0.0"
    }
  }
}

provider "oci" {
  region = var.region
}

provider "oci" {
  alias  = "home"
  region = element([for reg in data.oci_identity_region_subscriptions.region_subscriptions.region_subscriptions : reg if reg.is_home_region], 0).region_name
}
