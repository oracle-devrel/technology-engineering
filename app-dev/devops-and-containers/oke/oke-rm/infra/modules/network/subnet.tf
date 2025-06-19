
resource "oci_core_subnet" "service_subnet" {
  cidr_block     = var.service_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  prohibit_public_ip_on_vnic = var.service_subnet_private
  dns_label = var.service_subnet_dns_label
  display_name = var.service_subnet_name
  route_table_id = var.service_subnet_private ? oci_core_route_table.service_route_table.id : oci_core_route_table.internet_route_table[0].id
  count = local.create_service_subnet ? 1 : 0
}

resource "oci_core_subnet" "oke_cp_subnet" {
  cidr_block     = var.cp_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  dns_label = var.cp_subnet_dns_label
  display_name = var.cp_subnet_name
  prohibit_public_ip_on_vnic = var.cp_subnet_private
  route_table_id = var.cp_subnet_private ? local.cp_nat_mode ? oci_core_route_table.nat_route_table.id : oci_core_route_table.service_route_table.id : oci_core_route_table.internet_route_table[0].id
  count = local.create_cp_subnet ? 1 : 0
}

resource "oci_core_subnet" "worker_subnet" {
  cidr_block     = var.worker_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  dns_label = var.worker_subnet_dns_label
  display_name = var.worker_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id = oci_core_route_table.nat_route_table.id
  count = local.create_worker_subnet ? 1 : 0
}

resource "oci_core_subnet" "pods_subnet" {
  cidr_block     = var.pod_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  dns_label = var.pod_subnet_dns_label
  display_name = var.pod_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id = oci_core_route_table.nat_route_table.id
  count = local.create_pod_subnet ? 1 : 0
}

resource "oci_core_subnet" "bastion_subnet" {
  cidr_block     = var.bastion_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  dns_label = var.bastion_subnet_dns_label
  display_name = var.bastion_subnet_name
  prohibit_public_ip_on_vnic = var.bastion_subnet_private
  route_table_id = var.bastion_subnet_private ? oci_core_route_table.service_route_table.id : oci_core_route_table.internet_route_table[0].id
  security_list_ids = [oci_core_security_list.bastion_security_list.0.id]
  count = var.create_bastion_subnet ? 1 : 0
}

resource "oci_core_subnet" "fss_subnet" {
  cidr_block     = var.fss_subnet_cidr
  compartment_id = var.network_compartment_id
  vcn_id         = local.vcn_id
  dns_label = var.fss_subnet_dns_label
  display_name = var.fss_subnet_name
  prohibit_public_ip_on_vnic = true
  route_table_id = oci_core_route_table.service_route_table.id
  count = var.create_fss ? 1 : 0
}

