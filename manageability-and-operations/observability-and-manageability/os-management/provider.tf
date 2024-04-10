#terraform {
#  required_providers {
#    oci = {
#      source  = "oracle/oci"
#      version = ">= 4.0.0"
#    }
#  }
#}
provider "oci" {
  region              = var.region
  ignore_defined_tags = var.ignore_defined_tags
}
provider "oci" {
  alias               = "home"
  region              = lookup(local.region_map, data.oci_identity_tenancy.tenancy.home_region_key)
  ignore_defined_tags = var.ignore_defined_tags
}


data oci_identity_regions regions {}

data oci_identity_tenancy tenancy {
  tenancy_id = var.tenancy_ocid
}

locals {
  region_map = { for r in data.oci_identity_regions.regions.regions : r.key => r.name }
}

output home_region {
  value = lookup(local.region_map, data.oci_identity_tenancy.tenancy.home_region_key)
}
output target_region {
  value = var.region
}

output "compartment_ocid" {
  value = var.compartment_ocid
}

