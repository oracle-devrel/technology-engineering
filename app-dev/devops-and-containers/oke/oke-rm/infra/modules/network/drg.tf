resource "oci_core_drg" "vcn_drg" {
  compartment_id = var.network_compartment_id
  display_name   = var.drg_name

  count = local.create_drg ? 1 : 0
}

resource "oci_core_drg_attachment" "oke_drg_attachment" {
  drg_id       = local.drg_id
  display_name = var.vcn_name

  network_details {
    id   = local.vcn_id
    type = "VCN"
  }

  count = local.create_drg_attachment ? 1 : 0
}

