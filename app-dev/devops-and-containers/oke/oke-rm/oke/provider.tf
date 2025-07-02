terraform {
  required_version = ">=1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "7.4.0"
      configuration_aliases = [oci.home]
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.9.0"
    }
  }
}

provider "oci" {
  region = var.region
}

provider "oci" {
  alias = "home"
  #region = one(data.oci_identity_region_subscriptions.home.region_subscriptions[*].region_name)
  region = var.home_region
}