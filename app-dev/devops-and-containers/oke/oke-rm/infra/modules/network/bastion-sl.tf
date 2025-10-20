resource "oci_core_security_list" "bastion_security_list" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "bastion-sec-list"

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    protocol = local.tcp_protocol
    source_type = "CIDR_BLOCK"
    source   = "0.0.0.0/0"
    stateless = true
    description = "Allow SSH connections to the subnet. Can be deleted if only using OCI Bastion subnet"
    tcp_options {
      max = 22
      min = 22
    }
  }

  egress_security_rules {
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol = local.tcp_protocol
    stateless = true
    description = "Allow SSH responses from the subnet"
    tcp_options {
      source_port_range {
        max = 22
        min = 22
      }
    }
  }

  # Egress rules and their corresponding ingress
  egress_security_rules {
    destination = var.vcn_cidr_blocks[0]
    destination_type = "CIDR_BLOCK"
    protocol    = "all"
    stateless = true
    description = "Enable the bastion hosts to reach the entire VCN"
  }

  egress_security_rules {
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    protocol    = "all"
    stateless = false
    description = "Let bastion instances connect to Internet"
  }

  ingress_security_rules {
    protocol = "all"
    source_type = "CIDR_BLOCK"
    source = var.vcn_cidr_blocks[0]
    stateless = true
    description = "Allow responses from the VCN to the bastion hosts"
  }

  count = var.create_bastion_subnet ? 1 : 0
}
