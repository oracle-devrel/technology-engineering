variable "region" {}
variable "network_compartment_id" {}

# CNI TYPE

variable "cni_type" {}


# VCN

variable "create_vcn" {
  type = bool
}

variable "vcn_id" {}

variable "vcn_name" {
}

variable "vcn_cidr_blocks" {
  type = list(string)
}

variable "vcn_dns_label" {
}


# CP SUBNET

variable "create_cp_subnet" {
  type = bool
}

variable "cp_subnet_cidr" {
}

variable "cp_subnet_dns_label" {
}

variable "cp_subnet_name" {
}

variable "cp_subnet_private" {
  type = bool
}

variable "cp_allowed_source_cidr" {
}

variable "cp_external_nat" {}

variable "allow_external_cp_traffic" {
  type = bool
}

variable "cp_egress_cidr" {}

# WORKER SUBNET

variable "create_worker_subnet" {
  type = bool
}

variable "worker_subnet_cidr" {
}

variable "worker_subnet_dns_label" {
}

variable "worker_subnet_name" {
}

# POD SUBNET

variable "create_pod_subnet" {
  type = bool
}

variable "pod_subnet_cidr" {
}

variable "pod_subnet_dns_label" {
}

variable "pod_subnet_name" {
}

# LB SUBNETS

variable "create_external_lb_subnet" {
  type = bool
}

variable "external_lb_cidr" {
}

variable "external_lb_subnet_dns_label" {
}

variable "external_lb_subnet_name" {
}

variable "create_internal_lb_subnet" {
  type = bool
}

variable "internal_lb_cidr" {
}

variable "internal_lb_subnet_dns_label" {
}

variable "internal_lb_subnet_name" {
}


# BASTION SUBNET

variable "create_bastion_subnet" {
  type = bool
}

variable "bastion_subnet_private" {
  type = bool
}

variable "bastion_subnet_cidr" {
}

variable "bastion_subnet_dns_label" {
}

variable "bastion_subnet_name" {
}

# FSS

variable "create_fss" {
  type = bool
}

variable "fss_subnet_cidr" {}

variable "fss_subnet_dns_label" {}

variable "fss_subnet_name" {}

# GATEWAYS

variable "create_gateways" {
  type = bool
}

variable "create_internet_gateway" {
  type = bool
}

# DRG

variable "enable_drg" {
  type = bool
}

variable "create_drg" {
  type = bool
}

variable "drg_name" {}

variable "drg_id" {}

variable "create_drg_attachment" {
  type = bool
}

variable "peer_vcns" {
  type = list(string)
}