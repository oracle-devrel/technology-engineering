resource "oci_core_network_security_group" "cp_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "cp"
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress to OKE control plane from worker nodes"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_1_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress to worker nodes from control plane"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress for Kubernetes control plane inter-communication"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_2_stateless" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress for Kubernetes control plane inter-communication"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "CIDR_BLOCK"
  source = var.bastion_subnet_cidr
  stateless = true
  description = "Allow TCP ingress to kube-apiserver from the bastion subnet"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = var.create_bastion_subnet ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_3_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = var.bastion_subnet_cidr
  stateless = true
  description = "Allow TCP egress to bastion subnet from control plane"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
  count = var.create_bastion_subnet ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP ingress to OKE control plane from pods"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_4_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP egress to pods from control plane"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_5" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP ingress to kube-apiserver from pods"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_5_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP egress to pods from control plane"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_6" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress to kube-apiserver from worker nodes"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_6_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress to worker nodes from control plane"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_7" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "CIDR_BLOCK"
  source = var.cp_allowed_source_cidr
  stateless = true
  description = "Allow ingress traffic from specified sources"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_ingress_7_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = var.cp_allowed_source_cidr
  stateless = true
  description = "Allow TCP egress to specified sources from control plane"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_1_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress to OKE control plane from worker nodes for Kubelet responses"
  tcp_options {
    source_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_1" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress from OKE control plane to Kubelet on worker nodes"
  tcp_options {
    destination_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_2_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP ingress from pods to control plane for responses"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_2" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow TCP egress from OKE control plane to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_3_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "SERVICE_CIDR_BLOCK"
  source = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP ingress from OCI services to control plane for responses"
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_3" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "SERVICE_CIDR_BLOCK"
  destination = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP egress from OKE control plane to OCI services"
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_4_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP ingress from worker nodes to control plane for responses"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_4" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP egress from OKE control plane to worker nodes"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_5_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress from control plane to control plane for responses"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_5" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress for Kubernetes control plane inter-communication"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_egress_6" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "CIDR_BLOCK"
  destination = var.cp_egress_cidr
  stateless = false
  description = "Allow external traffic communication"
  count = local.create_cp_external_traffic_rule ? 1 : 0
}
