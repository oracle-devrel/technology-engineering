terraform {
  required_providers {
    oci = {
      configuration_aliases = [oci.home]
      source                = "oracle/oci"
      version               = ">= 5.4.0"
    }
  }

  required_version = ">= 1.2.0"
}