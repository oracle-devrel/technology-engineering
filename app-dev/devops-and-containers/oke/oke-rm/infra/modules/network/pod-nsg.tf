resource "oci_core_network_security_group" "pod_nsg" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "pod"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  count          = local.is_npn ? 1 : 0
}

# Pod intercommunication - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_pods_all_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow ALL ingress to pods from other pods"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_pods_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.pod_nsg.0.id
  stateless                 = true
  description               = "Allow ALL egress to other pods from pods"
  count                     = local.is_npn ? 1 : 0
}

# Cross-node communication - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_workers_all_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow ALL ingress to pods for cross-node pod communication when using NodePorts or hostNetwork: true"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_workers_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow ALL egress to workers from pods"
  count                     = local.is_npn ? 1 : 0
}

# Control plane webhooks - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_cp_all_ingress_webhooks" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow ALL ingress to pods from Kubernetes control plane for webhooks served by pods"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_cp_all_egress_webhooks" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow ALL egress to control plane from pods for webhooks served by pods"
  count                     = local.is_npn ? 1 : 0
}

# Load balancer - TCP
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_lb_tcp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress to pods from load balancers"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_lb_tcp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow TCP egress to load balancers from pods"
  count                     = local.is_npn ? 1 : 0
}

# Load balancer - UDP
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_lb_udp_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.udp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow UDP ingress to pods from load balancers"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_lb_udp_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.udp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.oke_lb_nsg.id
  stateless                 = true
  description               = "Allow UDP egress to load balancers from pods"
  count                     = local.is_npn ? 1 : 0
}

# Internet - ALL protocols
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_internet_all_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = "all"
  destination_type          = "CIDR_BLOCK"
  destination               = "0.0.0.0/0"
  stateless                 = false
  description               = "Allow ALL egress from pods to internet"
  count                     = local.is_npn && var.allow_pod_nat_egress ? 1 : 0
}

# Control plane - API server (TCP 6443)
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_cp_apiserver_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP egress from pods to Kubernetes API server on port 6443"
  tcp_options {
    destination_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_cp_apiserver_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.cp_nsg.id
  stateless                 = true
  description               = "Allow TCP ingress from control plane to pods on port 6443"
  tcp_options {
    source_port_range {
      max = 6443
      min = 6443
    }
  }
  count = local.is_npn ? 1 : 0
}

# OCI services - TCP
resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_services_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "SERVICE_CIDR_BLOCK"
  destination               = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP egress from pods to OCI Services"
  count                     = local.is_npn ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oke_pod_nsg_services_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "SERVICE_CIDR_BLOCK"
  source                    = local.service_cidr_block
  stateless                 = true
  description               = "Allow TCP ingress from OCI services to pods"
  count                     = local.is_npn ? 1 : 0
}

# POSTGRES

resource "oci_core_network_security_group_security_rule" "postgres_pod_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.postgres_service].id
  stateless                 = true
  description               = "Allow communication from pods to postgres"
  tcp_options {
    destination_port_range {
      max = 5432
      min = 5432
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "postgres_pod_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.postgres_service].id
  stateless                 = true
  description               = "Allow communication from postgres to pods"
  tcp_options {
    source_port_range {
      max = 5432
      min = 5432
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

# OCI CACHE

resource "oci_core_network_security_group_security_rule" "cache_pod_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.cache_service].id
  stateless                 = true
  description               = "Allow communication from pods to oci cache"
  tcp_options {
    destination_port_range {
      max = 6379
      min = 6379
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "cache_pod_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.cache_service].id
  stateless                 = true
  description               = "Allow communication from oci cache to pods"
  tcp_options {
    source_port_range {
      max = 6379
      min = 6379
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

# Oracle database

resource "oci_core_network_security_group_security_rule" "oracle_pod_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from pods to oracle database"
  tcp_options {
    destination_port_range {
      max = 1522
      min = 1521
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_pod_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from oracle database to pods"
  tcp_options {
    source_port_range {
      max = 1522
      min = 1521
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

# MySQL

resource "oci_core_network_security_group_security_rule" "mysql_classic_pod_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.mysql_service].id
  stateless                 = true
  description               = "Allow communication from pods to mysql classic database port"
  tcp_options {
    destination_port_range {
      max = 3306
      min = 3306
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "mysql_classic_pod_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.mysql_service].id
  stateless                 = true
  description               = "Allow communication from mysql classic database port to pods"
  tcp_options {
    source_port_range {
      max = 3306
      min = 3306
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}


resource "oci_core_network_security_group_security_rule" "mysql_x_pod_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.mysql_service].id
  stateless                 = true
  description               = "Allow communication from pods to mysql x database port"
  tcp_options {
    destination_port_range {
      max = 33060
      min = 33060
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "mysql_x_pod_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_nsg.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.mysql_service].id
  stateless                 = true
  description               = "Allow communication from mysql x database port to pods"
  tcp_options {
    source_port_range {
      max = 33060
      min = 33060
    }
  }
  count = local.is_npn && !var.separate_db_nsg && local.create_db_nsg && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}
