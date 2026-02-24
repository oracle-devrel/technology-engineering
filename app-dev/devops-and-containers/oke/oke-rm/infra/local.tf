locals {
  # VCN_NATIVE_CNI internally it is mapped as npn
  cni             = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  vcn_cidr_blocks = [var.vcn_cidr_block]
  tag_value       = var.tag_value == null ? { "freeformTags" = {}, "definedTags" = {} } : var.tag_value
  db_service_list = var.db_service_list == null ? [] : var.db_service_list
  subnets = {
    cidr = {
      pod         = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 1, 0) : null     # e.g., "10.0.0.0/17"
      worker      = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 3, 4) : null     # e.g., "10.0.128.0/19"
      lb_external = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 160) : null   # e.g., "10.0.160.0/24"
      lb_internal = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 161) : null   # e.g., "10.0.161.0/24"
      fss         = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 162) : null   # e.g., "10.0.162.0/24"
      db          = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 164) : null   # e.g., "10.0.164.0/24"
      msg         = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 8, 165) : null   # e.g., "10.0.165.0/24"
      bastion     = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 13, 5216) : null # e.g., "10.0.163.0/29"
      cp          = var.create_vcn ? cidrsubnet(var.vcn_cidr_block, 13, 5217) : null # e.g., "10.0.163.8/29"
    }
    dns = {
      pod         = "pod"
      worker      = "worker"
      lb_external = "lbext"
      lb_internal = "lbint"
      fss         = "fss"
      db          = "db"
      msg         = "msg"
      bastion     = "bastion"
      cp          = "cp"
    }
  }
}
