
resource "oci_core_subnet" "external_lb_subnet" {
  cidr_block                 = var.external_lb_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  prohibit_public_ip_on_vnic = false
  dns_label                  = var.external_lb_subnet_dns_label
  display_name               = var.external_lb_subnet_name
  route_table_id             = oci_core_route_table.lb_ext_route_table.0.id
  security_list_ids          = [oci_core_security_list.external_lb_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.external_lb_dhcp[0].id
  count                      = local.create_external_lb_subnet ? 1 : 0
}

resource "oci_core_subnet" "internal_lb_subnet" {
  cidr_block                 = var.internal_lb_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  prohibit_public_ip_on_vnic = true
  dns_label                  = var.internal_lb_subnet_dns_label
  display_name               = var.internal_lb_subnet_name
  route_table_id             = oci_core_route_table.lb_int_route_table.0.id
  security_list_ids          = [oci_core_security_list.internal_lb_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.internal_lb_dhcp[0].id
  count                      = local.create_internal_lb_subnet ? 1 : 0
}

resource "oci_core_subnet" "oke_cp_subnet" {
  cidr_block                 = var.cp_subnet_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  dns_label                  = var.cp_subnet_dns_label
  display_name               = var.cp_subnet_name
  prohibit_public_ip_on_vnic = var.cp_subnet_private
  route_table_id             = oci_core_route_table.cp_route_table.0.id
  security_list_ids          = [oci_core_security_list.cp_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.oke_cp_dhcp[0].id
  count                      = local.create_cp_subnet ? 1 : 0
}

resource "oci_core_subnet" "worker_subnet" {
  cidr_block                 = var.worker_subnet_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  dns_label                  = var.worker_subnet_dns_label
  display_name               = var.worker_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.worker_route_table.0.id
  security_list_ids          = [oci_core_security_list.worker_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.worker_dhcp[0].id
  count                      = local.create_worker_subnet ? 1 : 0
}

resource "oci_core_subnet" "pods_subnet" {
  cidr_block                 = var.pod_subnet_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  dns_label                  = var.pod_subnet_dns_label
  display_name               = var.pod_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.pod_route_table.0.id
  security_list_ids          = [oci_core_security_list.pod_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.pods_dhcp[0].id
  count                      = local.create_pod_subnet ? 1 : 0
}

resource "oci_core_subnet" "bastion_subnet" {
  cidr_block                 = var.bastion_subnet_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  dns_label                  = var.bastion_subnet_dns_label
  display_name               = var.bastion_subnet_name
  prohibit_public_ip_on_vnic = var.bastion_subnet_private
  route_table_id             = oci_core_route_table.bastion_route_table.0.id
  security_list_ids          = [oci_core_security_list.bastion_security_list.0.id]
  dhcp_options_id            = oci_core_dhcp_options.bastion_dhcp[0].id
  count                      = local.create_bastion_subnet ? 1 : 0
}

resource "oci_core_subnet" "fss_subnet" {
  cidr_block                 = var.fss_subnet_cidr
  compartment_id             = var.network_compartment_id
  vcn_id                     = local.vcn_id
  dns_label                  = var.fss_subnet_dns_label
  display_name               = var.fss_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.fss_route_table.0.id
  security_list_ids          = [oci_core_security_list.fss_sl.0.id]
  dhcp_options_id            = oci_core_dhcp_options.fss_dhcp[0].id
  count                      = local.create_fss_subnet ? 1 : 0
}
