resource "oci_core_network_security_group" "pod_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "pod-nsg"
  count = local.is_npn ? 1 : 0
}

# Ingress rules and their corresponding egress
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL ingress to pods from other pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_1_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL egress to other pods from pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL ingress to pods for cross-node pod communication when using NodePorts or hostNetwork: true"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_2_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL egress to workers from pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow ALL ingress to pods from Kubernetes control plane for webhooks served by pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_3_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow ALL egress to control plane from pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.icmp_protocol
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = true
  description = "Allow ICMP ingress to pods for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_4_stateless_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.icmp_protocol
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = true
  description = "Allow ICMP egress to internet from pods"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "pods_nsg_rule_lb_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "LBs to pods"
  count = local.is_npn ? 1 : 0
}

# Egress rules and their corresponding ingress
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_1" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = true
  description = "Allow ALL egress from pods to internet"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_1_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = true
  description = "Allow ALL ingress from internet to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_2" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL egress from pods for cross-node pod communication when using NodePorts or hostNetwork: true"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_2_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow ALL ingress from workers to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_3" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL egress from pods to other pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_3_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "Allow ALL ingress from other pods to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_4" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP egress from pods to Kubernetes API server"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_4_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = true
  description = "Allow TCP ingress from control plane to pods"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_5" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type = "SERVICE_CIDR_BLOCK"
  destination = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP egress from pods to OCI Services"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_5_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type = "SERVICE_CIDR_BLOCK"
  source = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = true
  description = "Allow TCP ingress from OCI services to pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_6" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.icmp_protocol
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = true
  description = "Allow ICMP egress from pods for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_6_stateless_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.icmp_protocol
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = true
  description = "Allow ICMP ingress from internet to pods"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}
