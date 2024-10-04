resource "oci_core_vcn" "export_sddc_vcn" {
    compartment_id = var.compartment_ocid
    cidr_block = var.vcn_cidr
    display_name = var.vcn_name
    dns_label = var.vcn_dns_label
}

