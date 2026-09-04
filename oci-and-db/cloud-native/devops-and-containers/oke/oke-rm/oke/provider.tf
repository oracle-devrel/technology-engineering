terraform {
  required_version = ">=1.5.0"
  required_providers {
    oci = {
      source                = "oracle/oci"
      version               = "8.19.0"
      configuration_aliases = [oci.home]
    }
    time = {
      source  = "hashicorp/time"
      version = "0.14.0"
    }
  }
}

provider "oci" {
  region = var.region
}

provider "oci" {
  alias  = "home"
  region = one(data.oci_identity_region_subscriptions.home.region_subscriptions[*].region_name)
}
