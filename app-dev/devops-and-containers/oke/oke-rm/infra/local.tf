locals {
  # VCN_NATIVE_CNI internally it is mapped as npn
  cni = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  vcn_cidr_blocks = [var.vcn_cidr_block]
  subnets = {
    cidr = {
      pod           = cidrsubnet(var.vcn_cidr_block, 1, 0)       # e.g., "10.1.0.0/17"
      worker        = cidrsubnet(var.vcn_cidr_block, 3, 4)       # e.g., "10.1.128.0/19"
      lb_external   = cidrsubnet(var.vcn_cidr_block, 8, 160)     # e.g., "10.1.160.0/24"
      lb_internal   = cidrsubnet(var.vcn_cidr_block, 8, 161)     # e.g., "10.1.161.0/24"
      fss           = cidrsubnet(var.vcn_cidr_block, 8, 162)     # e.g., "10.1.162.0/24"
      bastion       = cidrsubnet(var.vcn_cidr_block, 13, 5216)   # e.g., "10.1.163.0/29"
      cp            = cidrsubnet(var.vcn_cidr_block, 13, 5217)   # e.g., "10.1.163.8/29"
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
