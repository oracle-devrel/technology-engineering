resource "oci_core_security_list" "cp_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.cp_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_cp_subnet ? 1 : 0
}

resource "oci_core_security_list" "external_lb_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.external_lb_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_external_lb_subnet ? 1 : 0
}



resource "oci_core_security_list" "internal_lb_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.internal_lb_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_internal_lb_subnet ? 1 : 0
}


resource "oci_core_security_list" "worker_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.worker_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_worker_subnet ? 1 : 0
}

resource "oci_core_security_list" "pod_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.pod_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_pod_subnet ? 1 : 0
}


resource "oci_core_security_list" "fss_sl" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.fss_subnet_name

  # Ingress rules and their corresponding egress
  ingress_security_rules {
    description = "Required to enable Path MTU Discovery to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = "0.0.0.0/0"
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to enable Path MTU Discovery responses to work, and non-OCI communication"
    icmp_options {
      code = "4"
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = "0.0.0.0/0"
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  ingress_security_rules {
    description = "Required to allow application within VCN to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    source      = oci_core_vcn.spoke_vcn[0].cidr_block
    source_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  egress_security_rules {
    description = "Required to allow application within VCN responses to fail fast"
    icmp_options {
      type = "3"
    }
    protocol    = local.icmp_protocol
    destination = oci_core_vcn.spoke_vcn[0].cidr_block
    destination_type = "CIDR_BLOCK"
    stateless   = "true"
  }

  count = local.create_fss_subnet ? 1 : 0
}

resource "oci_core_security_list" "bastion_security_list" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.bastion_subnet_name

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

  count = local.create_bastion_subnet ? 1 : 0
}
