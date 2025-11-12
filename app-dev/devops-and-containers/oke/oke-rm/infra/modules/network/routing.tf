resource "oci_core_route_table" "bastion_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.bastion_subnet_name
  dynamic "route_rules" {
    for_each = var.bastion_subnet_private ? [0] : []
    content {
      network_entity_id = local.service_gateway_id
      destination_type = "SERVICE_CIDR_BLOCK"
      destination = local.service_cidr_block
      description = "Route for all internal OCI services in the region"
    }
  }
  dynamic "route_rules" {
    for_each = var.bastion_subnet_private ? [] : [0]
    content {
      network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
      destination_type = "CIDR_BLOCK"
      destination = "0.0.0.0/0"
      description = "Route to reach external Internet through the Internet gateway"
    }
  }
  dynamic "route_rules" {
    for_each = var.bastion_subnet_private ? [0] : []
    content {
      network_entity_id = local.nat_gateway_id
      destination_type = "CIDR_BLOCK"
      destination = "0.0.0.0/0"
      description = "Route to reach external Internet through a NAT gateway"
    }
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_route_table" "cp_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.cp_subnet_name
  dynamic "route_rules" {
    for_each = var.cp_subnet_private ? [0] : []
    content {
      network_entity_id = local.service_gateway_id
      destination_type = "SERVICE_CIDR_BLOCK"
      destination = local.service_cidr_block
      description = "Route for all internal OCI services in the region"
    }
  }
  dynamic "route_rules" {
    for_each = var.cp_subnet_private ? [] : [0]
    content {
      network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
      destination_type = "CIDR_BLOCK"
      destination = "0.0.0.0/0"
      description = "Route to reach external Internet through the Internet gateway"
    }
  }
  dynamic "route_rules" {
    for_each = local.cp_nat_mode ? [0] : []
    content {
      network_entity_id = local.nat_gateway_id
      destination_type = "CIDR_BLOCK"
      destination = "0.0.0.0/0"
      description = "Route to reach external Internet through a NAT gateway"
    }
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
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
  display_name = var.external_lb_subnet_name
  route_rules {
    network_entity_id = oci_core_internet_gateway.internet_gateway[0].id
    destination_type = "CIDR_BLOCK"
    destination = "0.0.0.0/0"
    description = "Route to reach external Internet through the Internet gateway"
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
    content {
      network_entity_id = local.drg_id
      destination_type  = "CIDR_BLOCK"
      destination       = route_rules.value
      description       = "Route to ${route_rules.value} through the DRG"
    }
  }
  count = local.create_external_lb_subnet ? 1 : 0
}

resource "oci_core_route_table" "lb_int_route_table" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name = var.internal_lb_subnet_name
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type = "SERVICE_CIDR_BLOCK"
    destination = local.service_cidr_block
    description = "Route for all internal OCI services in the region"
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
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
  display_name = var.worker_subnet_name
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type = "SERVICE_CIDR_BLOCK"
    destination = local.service_cidr_block
    description = "Route for all internal OCI services in the region"
  }
  route_rules {
    network_entity_id = local.nat_gateway_id
    destination_type = "CIDR_BLOCK"
    destination = "0.0.0.0/0"
    description = "Route to reach external Internet through a NAT gateway"
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
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
  display_name = var.pod_subnet_name
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type = "SERVICE_CIDR_BLOCK"
    destination = local.service_cidr_block
    description = "Route for all internal OCI services in the region"
  }
  route_rules {
    network_entity_id = local.nat_gateway_id
    destination_type = "CIDR_BLOCK"
    destination = "0.0.0.0/0"
    description = "Route to reach external Internet through a NAT gateway"
  }
  dynamic "route_rules" {
    for_each = var.enable_drg ? var.peer_vcns : []
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
  display_name = var.fss_subnet_name
  route_rules {
    network_entity_id = local.service_gateway_id
    destination_type = "SERVICE_CIDR_BLOCK"
    destination = local.service_cidr_block
    description = "Route for all internal OCI services in the region"
  }
  count = local.create_fss_subnet ? 1 : 0
}