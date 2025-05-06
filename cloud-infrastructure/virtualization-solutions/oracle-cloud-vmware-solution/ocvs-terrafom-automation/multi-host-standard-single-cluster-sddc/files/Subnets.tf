resource oci_core_subnet export_Subnet-OCVS {
  cidr_block     = var.subnet_esxi
  compartment_id = var.compartment_ocid
  display_name    = "Subnet ESXi Servers"
  dns_label       = "esxhosts"
  prohibit_public_ip_on_vnic = "true"
  vcn_id = oci_core_vcn.export_sddc_vcn.id
  security_list_ids = [
    oci_core_security_list.export_SecList-Subnet-OCVS.id
  ]
  route_table_id = oci_core_route_table.export_route_table_SDDC_Subnet.id
}
