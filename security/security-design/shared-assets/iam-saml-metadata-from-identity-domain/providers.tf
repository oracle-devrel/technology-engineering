provider "oci" {
  # Uses ~/.oci/config by default; select profile via var.oci_profile
  config_file_profile = var.oci_profile
}