resource "oci_core_network_security_group" "cp_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "cp"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
}

# Worker nodes to control plane - Kubelet communication (port 12250)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_kubelet_12250_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to OKE control plane from worker nodes on port 12250"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_kubelet_12250_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to worker nodes from control plane on port 12250"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
}

# Control plane inter-communication (port 6443)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_cp_internal_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress for Kubernetes control plane inter-communication on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_cp_internal_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP egress for Kubernetes control plane inter-communication on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

# Bastion subnet to control plane - API server (port 6443)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_bastion_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "CIDR_BLOCK"
  source                    = var.bastion_subnet_cidr
  stateless                 = true
  description               = "Allow TCP ingress to kube-apiserver from the bastion subnet on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_bastion_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = var.bastion_subnet_cidr
  stateless                 = true
  description               = "Allow TCP egress to bastion subnet from control plane on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

# Pods to control plane - Kubelet communication (port 12250)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_kubelet_12250_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP ingress to OKE control plane from pods on port 12250"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_kubelet_12250_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP egress to pods from control plane on port 12250"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
  count = local.is_npn ? 1 : 0
}

# Pods to control plane - API server (port 6443)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP ingress to kube-apiserver from pods on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP egress to pods from control plane on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

# Worker nodes to control plane - API server (port 6443)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to kube-apiserver from worker nodes on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to worker nodes from control plane on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

# External sources to control plane - API server (port 6443)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_external_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "CIDR_BLOCK"
  source                    = var.cp_allowed_source_cidr
  stateless                 = true
  description               = "Allow TCP ingress traffic from specified sources to kube-apiserver on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_external_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = var.cp_allowed_source_cidr
  stateless                 = true
  description               = "Allow TCP egress to specified sources from control plane on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

# Control plane to worker nodes - Kubelet (port 10250)
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_kubelet_10250_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to control plane from worker nodes for Kubelet responses on port 10250"
  tcp_options {
    source_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_worker_kubelet_10250_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from control plane to Kubelet on worker nodes on port 10250"
  tcp_options {
    destination_port_range {
      max = 10250
      min = 10250
    }
  }
}

# Control plane to pods - general communication
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP ingress from pods to control plane for responses"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_pods_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow TCP egress from control plane to pods"
  count                     = local.is_npn ? 1 : 0
}

# Control plane to OCI services
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_services_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "SERVICE_CIDR_BLOCK"
  source                    = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP ingress from OCI services to control plane for responses"
}

resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_services_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "SERVICE_CIDR_BLOCK"
  destination               = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP egress from control plane to OCI services"
}

# External traffic communication
resource "oci_core_network_security_group_security_rule" "oke_cp_nsg_external_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.cp_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = var.cp_egress_cidr
  stateless                 = false
  description               = "Allow external traffic communication"
  count                     = local.create_cp_external_traffic_rule ? 1 : 0
}
