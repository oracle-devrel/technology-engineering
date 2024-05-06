provider "oci" {
  alias               = "home"
  region              = var.home_region
  tenancy_ocid        = var.tenancy_id
}