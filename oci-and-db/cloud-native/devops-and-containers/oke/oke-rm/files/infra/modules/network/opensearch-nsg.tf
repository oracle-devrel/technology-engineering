locals {
  opensearch_ports = {
    api        = 9200
    dashboards = 5601
  }
  enabled_opensearch_ports = local.create_db_nsg && contains(var.db_service_list, "opensearch") ? local.opensearch_ports : {}
  opensearch_client_nsg_id = length(local.enabled_opensearch_ports) == 0 ? null : (
    local.create_app_db_nsg ? local.app_nsg.nsg_db["opensearch"].id : local.app_nsg.nsg_id
  )
}

# All endpoints share one database NSG and the existing pod/worker client selection.
# Stateless connections require explicit request and reply rules on both sides.
resource "oci_core_network_security_group_security_rule" "opensearch_db_ingress" {
  for_each                  = local.enabled_opensearch_ports
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.db["opensearch"].id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.opensearch_client_nsg_id
  stateless                 = true
  description               = "Allow applications to OpenSearch ${each.key}"
  tcp_options {
    destination_port_range {
      min = each.value
      max = each.value
    }
  }
}

resource "oci_core_network_security_group_security_rule" "opensearch_db_egress" {
  for_each                  = local.enabled_opensearch_ports
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.db["opensearch"].id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.opensearch_client_nsg_id
  stateless                 = true
  description               = "Allow OpenSearch ${each.key} replies to applications"
  tcp_options {
    source_port_range {
      min = each.value
      max = each.value
    }
  }
}

resource "oci_core_network_security_group_security_rule" "opensearch_client_egress" {
  for_each                  = local.enabled_opensearch_ports
  direction                 = "EGRESS"
  network_security_group_id = local.opensearch_client_nsg_id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = oci_core_network_security_group.db["opensearch"].id
  stateless                 = true
  description               = "Allow applications to OpenSearch ${each.key}"
  tcp_options {
    destination_port_range {
      min = each.value
      max = each.value
    }
  }
}

resource "oci_core_network_security_group_security_rule" "opensearch_client_ingress" {
  for_each                  = local.enabled_opensearch_ports
  direction                 = "INGRESS"
  network_security_group_id = local.opensearch_client_nsg_id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = oci_core_network_security_group.db["opensearch"].id
  stateless                 = true
  description               = "Allow OpenSearch ${each.key} replies to applications"
  tcp_options {
    source_port_range {
      min = each.value
      max = each.value
    }
  }
}
