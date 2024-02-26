resource oci_core_security_list export_SecList-Subnet-OCVS {
  compartment_id = var.compartment_ocid
  display_name = "Security List for Subnet-OCVS-Subnet"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
  egress_security_rules {
    description      = "Full Outbound Access"
    destination      = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol  = "all"
    stateless = "false"
  }
  ingress_security_rules {
    description = "Inbound Access from VCN"
    protocol    = "all"
    source      = var.vcn_cidr
    source_type = "CIDR_BLOCK"
    stateless   = "false"
  }
}