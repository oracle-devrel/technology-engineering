resource "oci_ocvp_esxi_host" "test_esxi_host" {
    cluster_id = var.SDDC_Cluster_OCID
    compute_availability_domain = var.AD
    display_name = var.ESXi_hostname
    host_shape_name = var.shape
    host_ocpu_count = var.OCPU_count
}
