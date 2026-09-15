data "oci_identity_region_subscriptions" "home" {
  tenancy_id = var.tenancy_ocid
  filter {
    name   = "is_home_region"
    values = [true]
  }
}

data "oci_core_subnet" "lb_subnet_data" {
  subnet_id = var.lb_subnet_id
}

data "oci_core_subnet" "cp_subnet_data" {
  subnet_id = var.cp_subnet_id
}