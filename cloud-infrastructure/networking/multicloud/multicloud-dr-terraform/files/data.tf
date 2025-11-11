##############################
# ------ Region Primary ---- #
##############################

data "oci_core_vcn" "vcn_primary" {
  provider = oci.region-primary
  vcn_id = var.vcn_primary_ocid
}

##############################
# ------ Region Standby ---- #
##############################

data "oci_core_vcn" "vcn_standby" {
  provider = oci.region-standby  
  vcn_id = var.vcn_standby_ocid
}