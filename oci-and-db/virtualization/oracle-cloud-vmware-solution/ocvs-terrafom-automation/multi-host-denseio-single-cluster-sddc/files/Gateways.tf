resource "oci_core_nat_gateway" "sddc_nat_gateway" {
    compartment_id = var.compartment_ocid
    vcn_id = oci_core_vcn.export_sddc_vcn.id
    display_name = "SDDC-NAT-Gateway"
}