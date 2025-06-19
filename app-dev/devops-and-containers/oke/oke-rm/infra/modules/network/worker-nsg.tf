resource "oci_core_network_security_group" "worker_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "worker-nsg"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow ALL ingress to workers from Kubernetes control plane for webhooks served by workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = false
  description = "Allow ALL ingress to workers from pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow ALL ingress to workers from other workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = false
  description = "Allow TCP ingress to workers for health check from public load balancers"
  tcp_options {
    destination_port_range {
      max = 10256
      min = 10256
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_5" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = false
  description = "Allow TCP ingress to workers from internal load balancers"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_6" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "1"
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = false
  description = "Allow ICMP ingress to workers for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_ingress_7" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  source_type = "CIDR_BLOCK"
  source = var.bastion_subnet_cidr
  stateless = false
  description = "Allow SSH access from bastion subnet"
  tcp_options {
    destination_port_range {
      max = 22
      min = 22
    }
  }
  count = var.create_bastion_subnet ? 1 : 0
}

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
  stateless = false
  description = "Allow ALL egress from workers to other workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_3" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = false
  description = "Allow ALL egress from workers to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_4" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow TCP egress from workers to Kubernetes API server"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_5" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "SERVICE_CIDR_BLOCK"
  destination = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = false
  description = "Allow TCP egress from workers to OCI Services"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_6" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow TCP egress to OKE control plane from workers for health check"
  tcp_options {
    destination_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_7" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow TCP egress from workers to OKE control plane"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_8" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "1"
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = false
  description = "Allow ICMP egress from workers for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_9" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "17"  # UDP
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = false
  description = "Allow UDP egress from workers for NFS portmapper to FSS mounts"
  udp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_10" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = false
  description = "Allow TCP egress from workers for NFS portmapper to FSS mounts"
  tcp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_11" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = false
  description = "Allow TCP egress from workers for NFS to FSS mounts"
  tcp_options {
    destination_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_12" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "17"  # UDP
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = false
  description = "Allow UDP egress from workers for NFS to FSS mounts"
  udp_options {
    destination_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_egress_13" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.fss_nsg.id
  stateless = false
  description = "Allow TCP egress from workers for NFS to FSS mounts when using in-transit encryption"
  tcp_options {
    destination_port_range {
      max = 2051
      min = 2051
    }
  }
}