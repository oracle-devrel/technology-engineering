resource "oci_core_network_security_group" "fss_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "fss-${var.network_resource_suffix}"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
}

# NFS Portmapper - UDP (port 111)
resource "oci_core_network_security_group_security_rule" "fss_workers_portmapper_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress for NFS portmapper from workers on port 111"
  udp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_workers_portmapper_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP egress for NFS portmapper to workers on port 111"
  udp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

# NFS Portmapper - TCP (port 111)
resource "oci_core_network_security_group_security_rule" "fss_workers_portmapper_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress for NFS portmapper from workers on port 111"
  tcp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_workers_portmapper_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress for NFS portmapper to workers on port 111"
  tcp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

# NFS - UDP (port 2048)
resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress for NFS from workers on port 2048"
  udp_options {
    destination_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow UDP egress for NFS to workers on port 2048"
  udp_options {
    source_port_range {
      max = 2048
      min = 2048
    }
  }
}

# NFS - TCP (ports 2048-2050)
resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress for NFS from workers on ports 2048-2050"
  tcp_options {
    destination_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress for NFS to workers on ports 2048-2050"
  tcp_options {
    source_port_range {
      max = 2050
      min = 2048
    }
  }
}

# NFS Encrypted - TCP (port 2051)
resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_encrypted_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress for NFS with in-transit encryption from workers on port 2051"
  tcp_options {
    destination_port_range {
      max = 2051
      min = 2051
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_workers_nfs_encrypted_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow TCP egress for NFS with in-transit encryption to workers on port 2051"
  tcp_options {
    source_port_range {
      max = 2051
      min = 2051
    }
  }
}

# Virtual Nodes and other directly addressed pods
resource "oci_core_network_security_group_security_rule" "fss_pods_tcp_ingress" {
  for_each                  = local.create_pod_fss_rules ? local.fss_tcp_port_ranges : {}
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg[0].id
  stateless                 = true
  description               = "Allow TCP ingress for ${each.value.description} from pods"
  tcp_options {
    destination_port_range {
      min = each.value.min
      max = each.value.max
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_pods_tcp_egress" {
  for_each                  = local.create_pod_fss_rules ? local.fss_tcp_port_ranges : {}
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg[0].id
  stateless                 = true
  description               = "Allow TCP egress for ${each.value.description} to pods"
  tcp_options {
    source_port_range {
      min = each.value.min
      max = each.value.max
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_pods_udp_ingress" {
  for_each                  = local.create_pod_fss_rules ? local.fss_udp_port_ranges : {}
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg[0].id
  stateless                 = true
  description               = "Allow UDP ingress for ${each.value.description} from pods"
  udp_options {
    destination_port_range {
      min = each.value.min
      max = each.value.max
    }
  }
}

resource "oci_core_network_security_group_security_rule" "fss_pods_udp_egress" {
  for_each                  = local.create_pod_fss_rules ? local.fss_udp_port_ranges : {}
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.fss_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg[0].id
  stateless                 = true
  description               = "Allow UDP egress for ${each.value.description} to pods"
  udp_options {
    source_port_range {
      min = each.value.min
      max = each.value.max
    }
  }
}
