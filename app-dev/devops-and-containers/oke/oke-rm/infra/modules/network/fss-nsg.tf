resource "oci_core_network_security_group" "fss_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "fss"
}

# Ingress rules and their corresponding egress
resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow UDP ingress for NFS portmapper from workers"
  udp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_1_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow UDP egress for NFS portmapper to workers"
  udp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress for NFS portmapper from workers"
  tcp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_2_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress for NFS portmapper to workers"
  tcp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow UDP ingress for NFS from workers"
  udp_options {
    destination_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_3_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow UDP egress for NFS to workers"
  udp_options {
    source_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress for NFS from workers"
  tcp_options {
    destination_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_4_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress for NFS to workers"
  tcp_options {
    source_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_5" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress when using in-transit encryption for OCI FSS"
  tcp_options {
    destination_port_range {
      max = 2051
      min = 2051
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_ingress_rule_5_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress when using in-transit encryption to workers"
  tcp_options {
    source_port_range {
      max = 2051
      min = 2051
    }
  }
}
