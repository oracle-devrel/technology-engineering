data "oci_identity_user" "current_user" {
  user_id = var.current_user_ocid
}

data "oci_identity_tenancy" "current_tenancy" {
  tenancy_id = var.tenancy_ocid
}

data "oci_identity_region_subscriptions" "region_subscriptions_data" {
  tenancy_id = var.tenancy_ocid
}