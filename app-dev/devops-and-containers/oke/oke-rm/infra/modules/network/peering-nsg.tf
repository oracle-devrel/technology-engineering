locals {
  # Only used when NSG exists
  peer_vcns_set = local.create_drg_attachment ? toset(var.peer_vcns) : []
}

resource "oci_core_network_security_group" "peering" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  display_name   = "peering"
  count          = local.create_drg_attachment && length(var.peer_vcns) > 0 ? 1 : 0
}

resource "oci_core_network_security_group_security_rule" "peering_egress" {
  for_each                  = local.peer_vcns_set
  direction                 = "EGRESS"
  network_security_group_id = oci_core_network_security_group.peering.0.id
  protocol                  = "all"
  destination_type          = "CIDR_BLOCK"
  destination               = each.value
  stateless                 = true
  description               = "Allow egress traffic to peered VCN ${each.value}"
}

resource "oci_core_network_security_group_security_rule" "peering_ingress" {
  for_each                  = local.peer_vcns_set
  direction                 = "INGRESS"
  network_security_group_id = oci_core_network_security_group.peering.0.id
  protocol                  = "all"
  source_type               = "CIDR_BLOCK"
  source                    = each.value
  stateless                 = true
  description               = "Allow ingress traffic from peered VCN ${each.value}"
}