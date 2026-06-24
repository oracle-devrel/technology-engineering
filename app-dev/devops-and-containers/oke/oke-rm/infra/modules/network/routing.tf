locals {
  peer_vcns_default_set     = local.create_drg_attachment ? toset([for cidr in var.peer_vcns : cidr if cidr == "0.0.0.0/0"]) : toset([])
  peer_vcns_non_default_set = local.create_drg_attachment ? toset([for cidr in var.peer_vcns : cidr if cidr != "0.0.0.0/0"]) : toset([])

  cp_has_default_route     = (!var.cp_subnet_private) || local.cp_nat_mode
  lb_int_has_default_route = false
  worker_has_default_route = local.create_nat_gateway && var.allow_worker_nat_egress
  pod_has_default_route    = local.create_nat_gateway && var.allow_pod_nat_egress

  cp_drg_peer_vcns     = setunion(local.peer_vcns_non_default_set, local.cp_has_default_route ? toset([]) : local.peer_vcns_default_set)
  lb_int_drg_peer_vcns = setunion(local.peer_vcns_non_default_set, local.lb_int_has_default_route ? toset([]) : local.peer_vcns_default_set)
  worker_drg_peer_vcns = setunion(local.peer_vcns_non_default_set, local.worker_has_default_route ? toset([]) : local.peer_vcns_default_set)
  pod_drg_peer_vcns    = setunion(local.peer_vcns_non_default_set, local.pod_has_default_route ? toset([]) : local.peer_vcns_default_set)
}

resource "oci_core_route_table" "bastion_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.bastion_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  dynamic "route_rules" {
    for_each = var.bastion_subnet_private ? [0] : []
    content {
      network_entity_id = local.service_gateway_id
      destination_type  = "SERVICE_CIDR_BLOCK"
      destination       = local.service_cidr_block
      description       = "Route for all internal OCI services in the region"
    }
  }
  dynamic "route_rules" {
    for_each = local.create_internet_gateway && !var.bastion_subnet_private ? [0] : []
    content {
      network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
      destination_type  = "CIDR_BLOCK"
      destination       = "0.0.0.0/0"
      description       = "Route to reach external Internet through the Internet gateway"
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_route_table" "cp_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.cp_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  dynamic "route_rules" {
    for_each = var.cp_subnet_private ? [0] : []
    content {
      network_entity_id = local.service_gateway_id
      destination_type  = "SERVICE_CIDR_BLOCK"
      destination       = local.service_cidr_block
      description       = "Route for all internal OCI services in the region"
    }
  }
  dynamic "route_rules" {
    for_each = var.cp_subnet_private ? [] : [0]
    content {
      network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
      destination_type  = "CIDR_BLOCK"
      destination       = "0.0.0.0/0"
      description       = "Route to reach external Internet through the Internet gateway"
    }
  }
  dynamic "route_rules" {
    for_each = local.cp_nat_mode ? [0] : []
    content {
      network_entity_id = local.nat_gateway_id
      destination_type  = "CIDR_BLOCK"
      destination       = "0.0.0.0/0"
      description       = "Route to reach external Internet through a NAT gateway"
    }
  }
  dynamic "route_rules" {
    for_each = local.cp_drg_peer_vcns
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_cp_subnet ? 1 : 0
}

resource "oci_core_route_table" "lb_ext_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.external_lb_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
    destination_type  = "CIDR_BLOCK"
    destination       = "0.0.0.0/0"
    description       = "Route to reach external Internet through the Internet gateway"
  }
  count = local.create_external_lb_subnet ? 1 : 0
}

resource "oci_core_route_table" "lb_int_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.internal_lb_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  dynamic "route_rules" {
    for_each = local.lb_int_drg_peer_vcns
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_internal_lb_subnet ? 1 : 0
}

resource "oci_core_route_table" "worker_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.worker_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  dynamic "route_rules" {
    for_each = local.create_nat_gateway && var.allow_worker_nat_egress ? [0] : []
    content {
      network_entity_id = local.nat_gateway_id
      destination_type  = "CIDR_BLOCK"
      destination       = "0.0.0.0/0"
      description       = "Route to reach external Internet through a NAT gateway"
    }
  }
  dynamic "route_rules" {
    for_each = local.worker_drg_peer_vcns
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_worker_subnet ? 1 : 0
}

resource "oci_core_route_table" "pod_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.pod_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  dynamic "route_rules" {
    for_each = local.create_nat_gateway && var.allow_pod_nat_egress ? [0] : []
    content {
      network_entity_id = local.nat_gateway_id
      destination_type  = "CIDR_BLOCK"
      destination       = "0.0.0.0/0"
      description       = "Route to reach external Internet through a NAT gateway"
    }
  }
  dynamic "route_rules" {
    for_each = local.pod_drg_peer_vcns
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_pod_subnet ? 1 : 0
}

resource "oci_core_route_table" "fss_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.fss_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  count = local.create_fss_subnet ? 1 : 0
}

resource "oci_core_route_table" "db_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.db_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  count = local.create_db_subnet ? 1 : 0
}

resource "oci_core_route_table" "msg_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.msg_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type  = "SERVICE_CIDR_BLOCK"
    destination       = local.service_cidr_block
    description       = "Route for all internal OCI services in the region"
  }
  count = local.create_msg_subnet ? 1 : 0
}
