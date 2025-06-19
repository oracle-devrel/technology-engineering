resource "oci_bastion_bastion" "vcn_spoke_bastion" {
  bastion_type     = "STANDARD"
  compartment_id   = var.compartment_id
  target_subnet_id = var.bastion_subnet_id
  name = "bastion-${var.vcn_name}"
  dns_proxy_status = "ENABLED"
  client_cidr_block_allow_list = var.bastion_cidr_block_allow_list
}