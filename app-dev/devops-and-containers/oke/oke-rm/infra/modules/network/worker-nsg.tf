resource "oci_core_network_security_group" "worker_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "worker"
}

# Ingress rules and their corresponding egress
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow ALL ingress to workers from Kubernetes control plane for webhooks served by workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_1_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow ALL egress to control plane from workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL ingress to workers from pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_2_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL egress to pods from workers"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL ingress to workers from other workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_3_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL egress to other workers from workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow TCP ingress to workers for health check from public load balancers"
  tcp_options {
    destination_port_range {
      max = 10256
      min = 10256
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_4_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow TCP egress to load balancers from workers"
  tcp_options {
    source_port_range {
      max = 10256
      min = 10256
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_5" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow TCP ingress to workers from load balancers"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_5_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow TCP egress to load balancers from workers"
  tcp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_udp" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow UDP ingress to workers from load balancers"
  udp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_udp_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Allow UDP egress to load balancers from workers"
  udp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}


resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_7" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "CIDR_BLOCK"
  source = var.bastion_subnet_cidr
  stateless = true
  description = "Allow SSH access from bastion subnet"
  tcp_options {
    destination_port_range {
      max = 22
      min = 22
    }
  }
  count = var.create_bastion_subnet ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_7_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = var.bastion_subnet_cidr
  stateless = true
  description = "Allow TCP egress to bastion from workers"
  tcp_options {
    source_port_range {
      max = 22
      min = 22
    }
  }
  count = var.create_bastion_subnet ? 1 : 0
}

# Egress rules and their corresponding ingress
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_1" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = false
  description = "Allow ALL egress from workers to internet"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_2" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL egress from workers to other workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_2_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL ingress from other workers to workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_3" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL egress from workers to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_3_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL ingress from pods to workers"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_4" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress from workers to Kubernetes API server"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_4_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress from control plane to workers"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_5" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "SERVICE_CIDR_BLOCK"
  destination = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP egress from workers to OCI Services"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_5_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "SERVICE_CIDR_BLOCK"
  source = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP ingress from OCI services to workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_6" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress to OKE control plane from workers for health check"
  tcp_options {
    destination_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_6_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress from control plane to workers"
  tcp_options {
    source_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_7" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress from workers to OKE control plane"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_7_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress from control plane to workers"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_8" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow UDP egress from workers for NFS portmapper to FSS mounts"
  udp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_8_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow UDP ingress from FSS to workers"
  udp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_9" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP egress from workers for NFS portmapper to FSS mounts"
  tcp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_9_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP ingress from FSS to workers"
  tcp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_10" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP egress from workers for NFS to FSS mounts"
  tcp_options {
    destination_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_10_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP ingress from FSS to workers"
  tcp_options {
    source_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_11" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow UDP egress from workers for NFS to FSS mounts"
  udp_options {
    destination_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_11_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow UDP ingress from FSS to workers"
  udp_options {
    source_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_12" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP egress from workers for NFS to FSS mounts when using in-transit encryption"
  tcp_options {
    destination_port_range {
      max = 2051
      min = 2051
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_12_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.fss_nsg.id
  stateless = true
  description = "Allow TCP ingress from FSS to workers"
  tcp_options {
    source_port_range {
      max = 2051
      min = 2051
    }
  }
}
