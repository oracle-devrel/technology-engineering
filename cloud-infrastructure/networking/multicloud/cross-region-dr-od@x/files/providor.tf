# ------ Initialize Oracle Terraform provider Primary Region
provider "oci" {
  alias            = "region-primary"
  user_ocid        = var.user_ocid
  private_key_path = var.private_key_path
  fingerprint      = var.fingerprint  
  region           = var.primary_region
  tenancy_ocid     = var.tenancy_ocid
}

# ------ Initialize Oracle Terraform provider Standby Region
provider "oci" {
  alias            = "region-standby"
  user_ocid        = var.user_ocid
  private_key_path = var.private_key_path
  fingerprint      = var.fingerprint  
  region           = var.standby_region
  tenancy_ocid     = var.tenancy_ocid
}