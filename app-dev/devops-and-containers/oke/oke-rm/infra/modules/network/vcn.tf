resource "oci_core_vcn" "spoke_vcn" {
  compartment_id = var.network_compartment_id
  display_name   = var.vcn_name
  cidr_blocks    = var.vcn_cidr_blocks
  dns_label      = var.vcn_dns_label
  count          = var.create_vcn ? 1 : 0
}

resource "oci_core_default_security_list" "lockdown" {
  manage_default_resource_id = oci_core_vcn.spoke_vcn.0.default_security_list_id

  lifecycle {
    ignore_changes = [defined_tags]
  }
  count = var.create_vcn ? 1 : 0
}
