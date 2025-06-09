terraform {
  required_version = ">=1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "7.4.0"
    }
    null = {
      source = "hashicorp/null"
      version = "3.2.4"
    }
    archive = {
      source = "hashicorp/archive"
      version = "2.7.1"
    }
    local = {
      source = "hashicorp/local"
      version = "2.5.3"
    }
  }
}

provider "oci" {
  region = var.region
}

provider "oci" {
  region = element([for reg in data.oci_identity_region_subscriptions.region_subscriptions_data.region_subscriptions : reg if reg.is_home_region ],0).region_name
  alias = "home"
}