resource "oci_core_network_security_group" "streaming" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  display_name   = "streaming"
  count          = var.create_streaming_nsg ? 1 : 0
}


resource "oci_core_network_security_group_security_rule" "streaming_kafka_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.streaming.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow communication from applications to OCI Streaming Kafka API"
  tcp_options {
    destination_port_range {
      max = 9092
      min = 9092
    }
  }
  count = var.create_streaming_nsg ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "streaming_kafka_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.streaming.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow communication from OCI Streaming Kafka API to applications"
  tcp_options {
    source_port_range {
      max = 9092
      min = 9092
    }
  }
  count = var.create_streaming_nsg ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "streaming_rest_ingress" {
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.streaming.0.id
  protocol                  = local.tcp_protocol
  source_type               = "NETWORK_SECURITY_GROUP"
  source                    = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow communication from applications to OCI Streaming REST API (SDK)"
  tcp_options {
    destination_port_range {
      max = 443
      min = 443
    }
  }
  count = var.create_streaming_nsg ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "streaming_rest_egress" {
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.streaming.0.id
  protocol                  = local.tcp_protocol
  destination_type          = "NETWORK_SECURITY_GROUP"
  destination               = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : oci_core_network_security_group.worker_nsg.id
  stateless                 = true
  description               = "Allow communication from OCI Streaming REST API (SDK) to applications"
  tcp_options {
    source_port_range {
      max = 443
      min = 443
    }
  }
  count = var.create_streaming_nsg ? 1 : 0
}