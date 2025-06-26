resource "oci_core_network_security_group" "oke_lb_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "oke-lb-nsg"
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow TCP traffic from load balancer to worker nodes for services of type NodePort"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}


resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_egress_udp" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.udp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow UDP traffic from load balancer to worker nodes for services of type NodePort"
  udp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_healthcheck_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow TCP egress from load balancers to worker nodes for health check"
  tcp_options {
    destination_port_range {
      max = 10256
      min = 10256
    }
  }
}


# OCI Native Ingress does not support UDP, hence no UDP egress rule
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_pods_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = false
  description = "LB to pods, OCI Native Ingress"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_worker_discovery_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.icmp_protocol
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow LB to discover workers"
  icmp_options {
    type = 3
    code = 4
  }
}