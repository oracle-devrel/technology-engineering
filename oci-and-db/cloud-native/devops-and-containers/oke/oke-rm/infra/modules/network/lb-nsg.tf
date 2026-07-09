resource "oci_core_network_security_group" "oke_lb_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "oke-lb-backend"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
}

# Worker nodes - Service ports TCP (30000-32767)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_service_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from load balancer to worker nodes for services of type NodePort on ports 30000-32767"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_service_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from worker nodes to load balancer for service responses on ports 30000-32767"
  tcp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

# Worker nodes - Service ports UDP (30000-32767)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_service_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP egress from load balancer to worker nodes for services of type NodePort on ports 30000-32767"
  udp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_service_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress from worker nodes to load balancer for service responses on ports 30000-32767"
  udp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

# Worker nodes - Health check (TCP 10256)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_healthcheck_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from load balancers to worker nodes for health check on port 10256"
  tcp_options {
    destination_port_range {
      max = 10256
      min = 10256
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_workers_healthcheck_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from worker nodes to load balancer for health check responses on port 10256"
  tcp_options {
    source_port_range {
      max = 10256
      min = 10256
    }
  }
}

# Pods - TCP (when NPN enabled)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_pods_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP egress from load balancer to pods for OCI Native Ingress and Pods as Backends"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_pods_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP ingress from pods to load balancer for responses"
  count                     = local.is_npn ? 1 : 0
}

# Pods - UDP (when NPN enabled)
resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_pods_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow UDP egress from load balancer to pods for OCI Native Ingress and Pods as Backends"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_lb_nsg_pods_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.oke_lb_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow UDP ingress from pods to load balancer for responses"
  count                     = local.is_npn ? 1 : 0
}
