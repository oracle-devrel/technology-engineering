resource "oci_core_network_security_group" "pod_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "pod-nsg"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_1" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = false
  description = "Allow ALL ingress to pods from other pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_2" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow ALL ingress to pods for cross-node pod communication when using NodePorts or hostNetwork: true"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_3" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow ALL ingress to pods from Kubernetes control plane for webhooks served by pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_ingress_4" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "1"
  source_type = "CIDR_BLOCK"
  source = "0.0.0.0/0"
  stateless = false
  description = "Allow ICMP ingress to pods for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "pods_nsg_rule_lb_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "6"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "LBs to pods, - stateless ingress"
  count = local.is_npn ? 1 : 0
}


resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_1" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = false
  description = "Allow ALL egress from pods to internet"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_2" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow ALL egress from pods for cross-node pod communication when using NodePorts or hostNetwork: true"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_3" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = false
  description = "Allow ALL egress from pods to other pods"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_4" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.cp_nsg.id
  stateless = false
  description = "Allow TCP egress from pods to Kubernetes API server"
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
  protocol                  = "6"
  destination_type = "SERVICE_CIDR_BLOCK"
  destination = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
  stateless = false
  description = "Allow TCP egress from pods to OCI Services"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_egress_6" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "1"
  destination_type = "CIDR_BLOCK"
  destination = "0.0.0.0/0"
  stateless = false
  description = "Allow ICMP egress from pods for path discovery"
  icmp_options {
    type = 3
    code = 4
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "pods_nsg_rule_lb_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.oke_lb_nsg.id
  stateless = true
  description = "Pods to LBs, - stateless egress"
  count = local.is_npn ? 1 : 0
}