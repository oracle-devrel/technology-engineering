resource "oci_core_network_security_group" "oke_lb_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = "oke-lb-nsg"
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP traffic from load balancer to worker nodes for services of type NodePort - stateless Egress"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "6"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.worker_nsg.id
  stateless = true
  description = "Allow TCP traffic from worker nodes to load balancer for services of type NodePort - stateless Ingress"
  tcp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_workers_healthcheck_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "6"
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

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_pods_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "6"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "LB to pods, OCI Native Ingress - stateless egress"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_pods_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "6"
  source_type = "NETWORK_SECURITY_GROUP"
  source = oci_core_network_security_group.pod_nsg.0.id
  stateless = true
  description = "LB to pods, OCI Native Ingress - stateless ingress"
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_rule_worker_discovery_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = "1"
  destination_type = "NETWORK_SECURITY_GROUP"
  destination = oci_core_network_security_group.worker_nsg.id
  stateless = false
  description = "Allow LB to discover workers"
  icmp_options {
    type = 3
    code = 4
  }
}