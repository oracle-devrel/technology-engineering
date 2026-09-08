variable "tenancy_ocid" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.tenancy\\.", var.tenancy_ocid))
    error_message = "tenancy_ocid must be a tenancy OCID."
  }
}

variable "region" {
  type = string
  validation {
    condition     = length(trimspace(var.region)) > 0
    error_message = "region must not be empty."
  }
}

variable "compartment_ocid" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.(compartment|tenancy)\\.", var.compartment_ocid))
    error_message = "compartment_ocid must be a compartment or tenancy OCID."
  }
}

variable "network_compartment_id" {
  type = string
  validation {
    condition     = can(regex("^ocid1\\.(compartment|tenancy)\\.", var.network_compartment_id))
    error_message = "network_compartment_id must be a compartment or tenancy OCID."
  }
}

variable "cni_type" {
  type    = string
  default = "vcn_native"
  validation {
    condition     = contains(["vcn_native", "flannel"], var.cni_type)
    error_message = "cni_type must be either vcn_native or flannel."
  }
}

# VCN
variable "create_vcn" {
  type    = bool
  default = true
}

variable "vcn_id" {
  type    = string
  default = null
  validation {
    condition     = var.vcn_id == null || can(regex("^ocid1\\.vcn\\.", var.vcn_id))
    error_message = "vcn_id must be null or a VCN OCID."
  }
}

variable "vcn_name" {
  default = "vcn-oke-1"
}

variable "vcn_cidr_block" {
  type    = string
  default = "10.0.0.0/16"
  validation {
    condition = can(cidrnetmask(var.vcn_cidr_block)) && contains(
      [16, 18, 20],
      try(tonumber(split("/", var.vcn_cidr_block)[1]), -1)
    ) && try(cidrhost(var.vcn_cidr_block, 0) == split("/", var.vcn_cidr_block)[0], false)
    error_message = "vcn_cidr_block must be a canonical IPv4 /16, /18, or /20 CIDR block."
  }
}

variable "vcn_dns_label" {
  type    = string
  default = "oke1"
  validation {
    condition     = can(regex("^[A-Za-z][A-Za-z0-9]{0,14}$", var.vcn_dns_label))
    error_message = "vcn_dns_label must start with a letter and contain at most 15 alphanumeric characters."
  }
}

# CP SUBNET

variable "create_cp_subnet" {
  type    = bool
  default = true
}

variable "cp_subnet_name" {
  default = "cp"
}

variable "cp_subnet_private" {
  type    = bool
  default = true
}

variable "cp_allowed_source_cidr" {
  type    = string
  default = "0.0.0.0/0"
  validation {
    condition     = can(cidrnetmask(var.cp_allowed_source_cidr))
    error_message = "cp_allowed_source_cidr must be a valid IPv4 CIDR block."
  }
}

# WORKER SUBNET

variable "create_worker_subnet" {
  type    = bool
  default = true
}

variable "worker_subnet_name" {
  default = "worker"
}

variable "allow_worker_nat_egress" {
  type    = bool
  default = true
}

# POD SUBNET

variable "create_pod_subnet" {
  type    = bool
  default = true
}

variable "pod_subnet_name" {
  default = "pod"
}

variable "allow_pod_nat_egress" {
  type    = bool
  default = true
}

variable "create_additional_pod_cidr" {
  type    = bool
  default = false
}

variable "additional_pod_cidr" {
  type    = list(string)
  default = []

  validation {
    condition     = length(var.additional_pod_cidr) <= 4 && alltrue([for cidr in var.additional_pod_cidr : can(cidrnetmask(cidr))])
    error_message = "additional_pod_cidr must contain at most four valid IPv4 CIDR blocks."
  }
}

# LB SUBNETS

variable "create_external_lb_subnet" {
  type    = bool
  default = true
}

variable "external_lb_subnet_name" {
  default = "lb-ext"
}

variable "create_internal_lb_subnet" {
  type    = bool
  default = true
}

variable "internal_lb_subnet_name" {
  default = "lb-int"
}

# BASTION SUBNET

variable "create_bastion_subnet" {
  type    = bool
  default = true
}

variable "bastion_subnet_private" {
  type    = bool
  default = false
}

variable "bastion_subnet_name" {
  default = "bastion"
}

# FSS SUBNET

variable "create_fss" {
  type    = bool
  default = true
}

variable "fss_subnet_name" {
  default = "fss"
}

variable "create_gateways" {
  type    = bool
  default = true
}

variable "create_internet_gateway" {
  type    = bool
  default = true
}

# CONTROL PLANE EXTERNAL CONNECTION

variable "cp_external_nat" {
  type    = bool
  default = true
}

variable "allow_external_cp_traffic" {
  type    = bool
  default = true
}

variable "cp_egress_cidr" {
  type    = string
  default = "0.0.0.0/0"
  validation {
    condition     = can(cidrnetmask(var.cp_egress_cidr))
    error_message = "cp_egress_cidr must be a valid IPv4 CIDR block."
  }
}

# ADDITIONAL NETWORK

variable "create_db_subnet" {
  type    = bool
  default = false
}

variable "db_subnet_name" {
  default = "db"
}

variable "db_service_list" {
  type    = list(string)
  default = []
  validation {
    condition     = alltrue([for service in var.db_service_list : contains(["postgres", "cache", "oracledb", "mysql"], service)])
    error_message = "db_service_list supports only postgres, cache, oracledb, and mysql."
  }
}

variable "create_database_nsgs" {
  type    = bool
  default = false
}

variable "separate_db_nsg" {
  type    = bool
  default = true
}

variable "create_msg_subnet" {
  type    = bool
  default = false
}

variable "msg_subnet_name" {
  default = "msg"
}

variable "create_streaming_nsg" {
  type    = bool
  default = false
}


# DRG

variable "enable_drg" {
  type    = bool
  default = false
}

variable "create_drg" {
  type    = bool
  default = true
}

variable "drg_id" {
  type    = string
  default = null
  validation {
    condition     = var.drg_id == null || can(regex("^ocid1\\.drg\\.", var.drg_id))
    error_message = "drg_id must be null or a DRG OCID."
  }
}

variable "drg_name" {
  default = null
}

variable "create_drg_attachment" {
  type    = bool
  default = true
}

variable "peer_vcns" {
  type    = list(string)
  default = []
  validation {
    condition     = alltrue([for cidr in var.peer_vcns : can(cidrnetmask(cidr))])
    error_message = "peer_vcns must contain valid IPv4 CIDR blocks."
  }
}

# Tagging

variable "tag_value" {
  type = object({
    freeformTags = map(string)
    definedTags  = map(string)
  })
  default = null
}
