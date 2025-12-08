locals {
  # VCN_NATIVE_CNI internally it is mapped as npn
  cni = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  vcn_cidr_blocks = [var.vcn_cidr_block]
  subnets = {
    cidr = {
      pod           = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 1, 0) : null       # e.g., "10.1.0.0/17"
      worker        = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 3, 4) : null       # e.g., "10.1.128.0/19"
      lb_external   = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 160) : null     # e.g., "10.1.160.0/24"
      lb_internal   = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 161) : null     # e.g., "10.1.161.0/24"
      fss           = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 162) : null     # e.g., "10.1.162.0/24"
      bastion       = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 13, 5216) : null   # e.g., "10.1.163.0/29"
      cp            = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 13, 5217) : null   # e.g., "10.1.163.8/29"
    }
    dns = {
      pod = "pod"
      worker = "worker"
      lb_external = "lbext"
      lb_internal = "lbint"
      fss = "fss"
      bastion = "bastion"
      cp = "cp"
    }
  }
}
