resource "oci_core_network_security_group" "worker_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  display_name   = "worker"
}

# Control plane - ALL protocols (webhooks)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_all_ingress_webhooks" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow ALL ingress to workers from Kubernetes control plane for webhooks served by workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_all_egress_webhooks" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow ALL egress to control plane from workers for webhooks served by workers"
}

# Pods - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_pods_all_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow ALL ingress to workers from pods"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_pods_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow ALL egress to pods from workers"
  count                     = local.is_npn ? 1 : 0
}

# Worker intercommunication - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_workers_all_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow ALL ingress to workers from other workers"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_workers_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow ALL egress to other workers from workers"
}

# Load balancer - Health check (TCP 10256)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_healthcheck_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to workers for health check from public load balancers on port 10256"
  tcp_options {
    destination_port_range {
      max = 10256
      min = 10256
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_healthcheck_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to load balancers from workers on port 10256"
  tcp_options {
    source_port_range {
      max = 10256
      min = 10256
    }
  }
}

# Load balancer - Service ports TCP (30000-32767)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_service_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to workers from load balancers on service ports 30000-32767"
  tcp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_service_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to load balancers from workers on service ports 30000-32767"
  tcp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

# Load balancer - Service ports UDP (30000-32767)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_service_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress to workers from load balancers on service ports 30000-32767"
  udp_options {
    destination_port_range {
      max = 32767
      min = 30000
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_lb_service_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow UDP egress to load balancers from workers on service ports 30000-32767"
  udp_options {
    source_port_range {
      max = 32767
      min = 30000
    }
  }
}

# Bastion - SSH access (TCP 22)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_bastion_ssh_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "CIDR_BLOCK"
  source                    = var.bastion_subnet_cidr
  stateless                 = true
  description               = "Allow SSH access from bastion subnet on port 22"
  tcp_options {
    destination_port_range {
      max = 22
      min = 22
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_bastion_ssh_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "CIDR_BLOCK"
  destination               = var.bastion_subnet_cidr
  stateless                 = true
  description               = "Allow TCP egress to bastion from workers on port 22"
  tcp_options {
    source_port_range {
      max = 22
      min = 22
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

# Internet - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_internet_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = "all"
  destination_type          = "CIDR_BLOCK"
  destination               = "0.0.0.0/0"
  stateless                 = false
  description               = "Allow ALL egress from workers to internet"
  count                     = var.allow_worker_nat_egress ? 1 : 0
}

# Control plane - API server (TCP 6443)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from workers to Kubernetes API server on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from control plane to workers on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
}

# OCI services - TCP
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_services_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "SERVICE_CIDR_BLOCK"
  destination               = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP egress from workers to OCI Services"
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_services_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "SERVICE_CIDR_BLOCK"
  source                    = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP ingress from OCI services to workers"
}

# Control plane - Kubelet health check (TCP 10250)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_kubelet_health_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to control plane from workers for health check on port 10250"
  tcp_options {
    destination_port_range {
      max = 10250
      min = 10250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_kubelet_health_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from control plane to workers on port 10250"
  tcp_options {
    source_port_range {
      max = 10250
      min = 10250
    }
  }
}

# Control plane - Kubelet (TCP 12250)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_kubelet_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from workers to control plane on port 12250"
  tcp_options {
    destination_port_range {
      max = 12250
      min = 12250
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_cp_kubelet_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from control plane to workers on port 12250"
  tcp_options {
    source_port_range {
      max = 12250
      min = 12250
    }
  }
}

# FSS - NFS portmapper UDP (111)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_portmapper_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow UDP egress from workers for NFS portmapper to FSS mounts on port 111"
  udp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_portmapper_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress from FSS to workers on port 111"
  udp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

# FSS - NFS portmapper TCP (111)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_portmapper_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from workers for NFS portmapper to FSS mounts on port 111"
  tcp_options {
    destination_port_range {
      max = 111
      min = 111
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_portmapper_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from FSS to workers on port 111"
  tcp_options {
    source_port_range {
      max = 111
      min = 111
    }
  }
}

# FSS - NFS TCP (2048-2050)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from workers for NFS to FSS mounts on ports 2048-2050"
  tcp_options {
    destination_port_range {
      max = 2050
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from FSS to workers on ports 2048-2050"
  tcp_options {
    source_port_range {
      max = 2050
      min = 2048
    }
  }
}

# FSS - NFS UDP (2048)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow UDP egress from workers for NFS to FSS mounts on port 2048"
  udp_options {
    destination_port_range {
      max = 2048
      min = 2048
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress from FSS to workers on port 2048"
  udp_options {
    source_port_range {
      max = 2048
      min = 2048
    }
  }
}

# FSS - NFS encrypted TCP (2051)
resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_encrypted_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from workers for NFS to FSS mounts when using in-transit encryption on port 2051"
  tcp_options {
    destination_port_range {
      max = 2051
      min = 2051
    }
  }
}

resource "oci_core_network_security_group_security_rule" "oke_worker_nsg_fss_nfs_encrypted_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.fss_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from FSS to workers on port 2051"
  tcp_options {
    source_port_range {
      max = 2051
      min = 2051
    }
  }
}

# POSTGRES

resource "oci_core_network_security_group_security_rule" "postgres_worker_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.postgres_service].id
  stateless                 = true
  description               = "Allow communication from worker nodes to postgres"
  tcp_options {
    destination_port_range {
      max = 5432
      min = 5432
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "postgres_worker_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.postgres_service].id
  stateless                 = true
  description               = "Allow communication from postgres to worker nodes"
  tcp_options {
    source_port_range {
      max = 5432
      min = 5432
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

# OCI CACHE

resource "oci_core_network_security_group_security_rule" "cache_worker_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.cache_service].id
  stateless                 = true
  description               = "Allow communication from workers to oci cache"
  tcp_options {
    destination_port_range {
      max = 6379
      min = 6379
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "cache_worker_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.cache_service].id
  stateless                 = true
  description               = "Allow communication from oci cache to workers"
  tcp_options {
    source_port_range {
      max = 6379
      min = 6379
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

# Oracle database

resource "oci_core_network_security_group_security_rule" "oracle_worker_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from workers to oracle database"
  tcp_options {
    destination_port_range {
      max = 1522
      min = 1521
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_worker_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.worker_nsg.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from oracle database to workers"
  tcp_options {
    source_port_range {
      max = 1522
      min = 1521
    }
  }
  count = !local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}