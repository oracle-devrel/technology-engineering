locals {
  create_db_nsg = local.create_db_subnet || ! var.create_vcn
  app_nsg_lookup = {
    npn = {
      nsg_id = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : null
      nsg_db = oci_core_network_security_group.pod_db
    }
    flannel = {
      nsg_id = oci_core_network_security_group.worker_nsg.id
      nsg_db = oci_core_network_security_group.worker_db
    }
  }
  app_nsg = local.is_npn ? local.app_nsg_lookup.npn : local.app_nsg_lookup.flannel
}

resource "oci_core_network_security_group" "db" {
  for_each       = local.create_db_nsg ? toset(var.db_service_list) : []
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  display_name   = each.value
}

# POSTGRES

resource "oci_core_network_security_group_security_rule" "postgres_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.postgres_service].id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.postgres_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from applications to postgres"
  tcp_options {
    destination_port_range {
      max = 5432
      min = 5432
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "postgres_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.postgres_service].id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.postgres_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from applications to pods"
  tcp_options {
    source_port_range {
      max = 5432
      min = 5432
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

# OCI Cache

resource "oci_core_network_security_group_security_rule" "cache_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.cache_service].id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.cache_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from pods to oci cache"
  tcp_options {
    destination_port_range {
      max = 6379
      min = 6379
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "cache_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.cache_service].id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.cache_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from oci cache to pods"
  tcp_options {
    source_port_range {
      max = 6379
      min = 6379
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

# Oracle Database

resource "oci_core_network_security_group_security_rule" "oracle_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.oracledb_service].id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.oracledb_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from pods to oracle database"
  tcp_options {
    destination_port_range {
      max = 1522
      min = 1521
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.db[local.oracledb_service].id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.create_app_db_nsg ? local.app_nsg.nsg_db[local.oracledb_service].id : local.app_nsg.nsg_id
  stateless                 = true
  description               = "Allow communication from oracle database to pods"
  tcp_options {
    source_port_range {
      max = 1522
      min = 1521
    }
  }
  count = local.create_db_nsg && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}