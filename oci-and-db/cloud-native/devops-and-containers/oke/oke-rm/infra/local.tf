locals {
  # VCN_NATIVE_CNI internally it is mapped as npn
  cni             = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  vcn_cidr_blocks = [var.vcn_cidr_block]
  tag_value       = var.tag_value == null ? { "freeformTags" = {}, "definedTags" = {} } : var.tag_value
  db_service_list = var.db_service_list == null ? [] : var.db_service_list

  vcn_cidr_prefix = tonumber(split("/", trimspace(var.vcn_cidr_block))[1])
  subnet_profile_by_cidr = {
    "16" = "large"
    "18" = "medium"
    "20" = "small"
  }
  subnet_profile = lookup(local.subnet_profile_by_cidr, tostring(local.vcn_cidr_prefix), "large")
  is_large       = local.subnet_profile == "large"
  is_medium      = local.subnet_profile == "medium"
  is_small       = local.subnet_profile == "small"

  subnet_profiles = {
    large = {
      # Assumes /16 base VCN (e.g., 10.0.0.0/16). Used IPs: 49936. Remaining free IPs: 15600.
      cidr = {
        pod         = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 1, 0) : null     # e.g., "10.0.0.0/17"
        worker      = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 3, 4) : null     # e.g., "10.0.128.0/19"
        lb_external = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 8, 160) : null   # e.g., "10.0.160.0/24"
        lb_internal = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 8, 161) : null   # e.g., "10.0.161.0/24"
        fss         = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 8, 162) : null   # e.g., "10.0.162.0/24"
        db          = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 8, 164) : null   # e.g., "10.0.164.0/24"
        msg         = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 8, 165) : null   # e.g., "10.0.165.0/24"
        bastion     = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 13, 5216) : null # e.g., "10.0.163.0/29"
        cp          = var.create_vcn && local.is_large ? cidrsubnet(var.vcn_cidr_block, 13, 5217) : null # e.g., "10.0.163.8/29"
      }
    }
    medium = {
      # Assumes /18 base VCN (e.g., 10.0.0.0/18). Used IPs: 9872. Remaining free IPs: 6512.
      cidr = {
        pod         = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 1, 0) : null     # e.g., "10.0.0.0/19"
        worker      = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 4, 8) : null     # e.g., "10.0.32.0/22"
        lb_external = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 7, 72) : null    # e.g., "10.0.36.0/25"
        lb_internal = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 7, 73) : null    # e.g., "10.0.36.128/25"
        fss         = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 7, 74) : null    # e.g., "10.0.37.0/25"
        db          = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 7, 75) : null    # e.g., "10.0.37.128/25"
        msg         = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 7, 76) : null    # e.g., "10.0.38.0/25"
        bastion     = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 11, 1248) : null # e.g., "10.0.39.0/29"
        cp          = var.create_vcn && local.is_medium ? cidrsubnet(var.vcn_cidr_block, 11, 1249) : null # e.g., "10.0.39.8/29"
      }
    }
    small = {
      # Assumes /20 base VCN (e.g., 10.0.0.0/20). Used IPs: 2896. Remaining free IPs: 1200.
      cidr = {
        pod         = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 1, 0) : null   # e.g., "10.0.0.0/21"
        worker      = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 3, 4) : null   # e.g., "10.0.8.0/23"
        lb_external = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 6, 40) : null  # e.g., "10.0.10.0/26"
        lb_internal = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 6, 41) : null  # e.g., "10.0.10.64/26"
        fss         = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 6, 42) : null  # e.g., "10.0.10.128/26"
        db          = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 6, 43) : null  # e.g., "10.0.10.192/26"
        msg         = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 6, 44) : null  # e.g., "10.0.11.0/26"
        bastion     = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 9, 360) : null # e.g., "10.0.11.64/29"
        cp          = var.create_vcn && local.is_small ? cidrsubnet(var.vcn_cidr_block, 9, 361) : null # e.g., "10.0.11.72/29"
      }
    }
  }
  subnets = {
    cidr = local.subnet_profiles[local.subnet_profile].cidr
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
