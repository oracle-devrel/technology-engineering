data "oci_identity_availability_domains" "export_availability_domains" {
    compartment_id = var.compartment_ocid
}