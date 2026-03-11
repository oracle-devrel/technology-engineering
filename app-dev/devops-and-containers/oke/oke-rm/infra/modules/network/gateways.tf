resource "oci_core_service_gateway" "service_gateway" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "SG"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  services {
    service_id = lookup(data.oci_core_services.all_oci_services.services[0], "id")
  }
  count = local.create_gateways ? 1 : 0
}

resource "oci_core_nat_gateway" "nat_gateway" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "NAT"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  count          = local.create_nat_gateway ? 1 : 0
}

resource "oci_core_internet_gateway" "internet_gateway" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = "IGW"
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  count          = local.create_internet_gateway ? 1 : 0
}