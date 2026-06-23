
terraform {
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 7.0.0"
    }
  }
  required_version = ">= 1.12"
  backend "oci" {
    bucket    = "TerraformStates"
    namespace = "frxfz3gch4zb"    # oci os ns get
    key       = "OSManagementHub/terraform.tfstate"
    region    = "eu-frankfurt-1"
  }
}

provider "oci" {
  config_file_profile = "oci4cca"
  region              = var.region
}

#provider "oci" {
#  tenancy_ocid     = var.tenancy_ocid
#  user_ocid        = var.user_id
#  fingerprint      = var.fingerprint
#  private_key_path = var.private_key_path
#  region           = var.region
#}
