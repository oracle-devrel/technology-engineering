resource "oci_core_vcn" "spoke_vcn" {
  compartment_id = var.network_compartment_id
  display_name = var.vcn_name
  cidr_blocks = var.vcn_cidr_blocks
  dns_label = var.vcn_dns_label
  count = var.create_vcn ? 1 : 0
}

resource "oci_core_default_security_list" "lockdown" {
  manage_default_resource_id = oci_core_vcn.spoke_vcn.0.default_security_list_id
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = "1"
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "false"
  }
  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = "1"
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "false"
  }
  lifecycle {
    ignore_changes = [egress_security_rules, ingress_security_rules, defined_tags]
  }
  count = var.create_vcn ? 1 : 0
}