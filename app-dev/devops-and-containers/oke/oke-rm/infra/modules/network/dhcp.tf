resource "oci_core_dhcp_options" "external_lb_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.external_lb_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_external_lb_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "internal_lb_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.internal_lb_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_internal_lb_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "oke_cp_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.cp_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_cp_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "worker_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.worker_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_worker_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "pods_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.pod_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_pod_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "bastion_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.bastion_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "fss_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.fss_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_fss_subnet ? 1 : 0
}

resource "oci_core_dhcp_options" "db_dhcp" {
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  display_name   = var.db_subnet_name
  freeform_tags  = var.tag_value.freeformTags
  defined_tags   = var.tag_value.definedTags
  options {
    type        = "DomainNameServer"
    server_type = "VcnLocalPlusInternet"
  }
  count = local.create_db_subnet ? 1 : 0
}
