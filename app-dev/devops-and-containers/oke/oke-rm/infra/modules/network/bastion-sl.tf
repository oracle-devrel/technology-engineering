resource "oci_core_security_list" "bastion_security_list" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "bastion-sec-list"
  ingress_security_rules {
    protocol = "6"
    source_type = "CIDR_BLOCK"
    source   = "0.0.0.0/0"
    description = "Allow SSH connections to the subnet. Can be deleted if only using OCI Bastion subnet"
    tcp_options {
      max = 22
      min = 22
    }
  }
  egress_security_rules {
    destination = var.vcn_cidr_blocks[0]
    destination_type = "CIDR_BLOCK"
    protocol    = "all"
    description = "Enable the bastion hosts to reach the entire VCN"
  }
  count = var.create_bastion_subnet ? 1 : 0
}