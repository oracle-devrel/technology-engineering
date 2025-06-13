locals {
  create_bastion = var.create_bastion_subnet && var.create_bastion
  # VCN_NATIVE_CNI internally it is mapped as npn
  cni = var.cni_type == "vcn_native" ? "npn" : var.cni_type
}
