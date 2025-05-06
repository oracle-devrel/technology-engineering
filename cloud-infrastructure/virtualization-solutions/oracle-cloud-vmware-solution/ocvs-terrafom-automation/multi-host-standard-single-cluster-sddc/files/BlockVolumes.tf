resource "oci_core_volume" "export_VMFS_Management_datastore_volume" {
    compartment_id = var.compartment_ocid
    availability_domain = data.oci_identity_availability_domains.export_availability_domains.availability_domains[0].name
    display_name = "ds-sda-MGMT-LUN"
    size_in_gbs = 8192  # NEEDS TO BE MIN 8TB! This is for all the VMware Management VMs, like vCenter
    vpus_per_gb = 10
}

resource "oci_core_volume" "export_VMFS_datastore_volume" {
    compartment_id = var.compartment_ocid
    availability_domain = data.oci_identity_availability_domains.export_availability_domains.availability_domains[0].name
    display_name = var.SDDC_BlockVolume_name
    size_in_gbs = var.SDDC_BlockVolume_SizeInGB
    vpus_per_gb = var.SDDC_BlockVolume_VPUs
}