locals {
  create_pod_db = local.create_app_db_nsg && local.is_npn
}

resource "oci_core_network_security_group" "pod_db" {
  for_each       = local.create_pod_db ? toset(var.db_service_list) : []
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  display_name   = "pod-${each.value}"
}


# POSTGRES

resource "oci_core_network_security_group_security_rule" "postgres_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.postgres_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "postgres_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.postgres_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.postgres_service) ? 1 : 0
}

# OCI CACHE

resource "oci_core_network_security_group_security_rule" "cache_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.cache_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "cache_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.cache_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.cache_service) ? 1 : 0
}

# Oracle database

resource "oci_core_network_security_group_security_rule" "oracle_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.oracledb_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.oracledb_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_mongo_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.oracledb_service].id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from pods to oracle mongodb API"
  tcp_options {
    destination_port_range {
      max = 27017
      min = 27017
    }
  }
  count = local.create_pod_db && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "oracle_mongo_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.oracledb_service].id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db[local.oracledb_service].id
  stateless                 = true
  description               = "Allow communication from oracle mongodb API to pods"
  tcp_options {
    source_port_range {
      max = 27017
      min = 27017
    }
  }
  count = local.create_pod_db && contains(var.db_service_list, local.oracledb_service) ? 1 : 0
}

# MySQL

resource "oci_core_network_security_group_security_rule" "mysql_classic_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.mysql_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "mysql_classic_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.mysql_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "mysql_x_pod_db_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.mysql_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "mysql_x_pod_db_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.pod_db[local.mysql_service].id
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
  count = local.create_pod_db && contains(var.db_service_list, local.mysql_service) ? 1 : 0
}