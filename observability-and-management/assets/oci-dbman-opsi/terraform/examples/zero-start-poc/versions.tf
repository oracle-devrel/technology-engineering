terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 6.0.0"
    }
  }
}

provider "oci" {
  region = var.region
  # Use a named ~/.oci/config profile (e.g. "cap" staging) so plan/apply run in the
  # intended tenancy. Defaults to DEFAULT; override via the config_file_profile var.
  config_file_profile = var.config_file_profile
}

