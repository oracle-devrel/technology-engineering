variable "tenancy_ocid" {}
variable "region" {}
variable "compartment_ocid" {}
variable "network_compartment_id" {}

variable "cni_type" {
  default = "flannel"
}

# VCN
variable "create_vcn" {
  type = bool
  default = true
}

variable "vcn_id" {
  default = null
}

variable "vcn_name" {
  default = "vcn-oke-1"
}

variable "vcn_cidr_blocks" {
  type = list(string)
  default = ["10.1.0.0/16"]
}

variable "vcn_dns_label" {
  default = "oke1"
}

# CP SUBNET

variable "create_cp_subnet" {
  type = bool
  default = true
}

variable "cp_subnet_cidr" {
  default = "10.1.163.8/29"
}

variable "cp_subnet_dns_label" {
  default = "cp"
}

variable "cp_subnet_name" {
  default = "cp"
}

variable "cp_subnet_private" {
  type = bool
  default = true
}

variable "cp_allowed_source_cidr" {
  default = "0.0.0.0/0"
}

# WORKER SUBNET

variable "create_worker_subnet" {
  type = bool
  default = true
}

variable "worker_subnet_cidr" {
  default = "10.1.128.0/19"
}

variable "worker_subnet_dns_label" {
  default = "worker"
}

variable "worker_subnet_name" {
  default = "worker"
}

# POD SUBNET

variable "create_pod_subnet" {
  type = bool
  default = true
}

variable "pod_subnet_cidr" {
  default = "10.1.0.0/17"
}

variable "pod_subnet_dns_label" {
  default = "pod"
}

variable "pod_subnet_name" {
  default = "pod"
}

# LB SUBNETS

variable "create_external_lb_subnet" {
  type = bool
  default = false
}

variable "external_lb_subnet_cidr" {
  default = "10.1.160.0/24"
}

variable "external_lb_subnet_dns_label" {
  default = "lbext"
}

variable "external_lb_subnet_name" {
  default = "lb-ext"
}

variable "create_internal_lb_subnet" {
  type = bool
  default = true
}

variable "internal_lb_subnet_cidr" {
  default = "10.1.161.0/24"
}

variable "internal_lb_subnet_dns_label" {
  default = "lbint"
}

variable "internal_lb_subnet_name" {
  default = "lb-int"
}

# BASTION SUBNET

variable "create_bastion_subnet" {
  type = bool
  default = true
}

variable "bastion_subnet_cidr" {
  default = "10.1.163.0/29"
}

variable "bastion_subnet_private" {
  type = bool
  default = false
}

variable "bastion_subnet_dns_label" {
  default = "bastion"
}

variable "bastion_subnet_name" {
  default = "bastion"
}

# FSS SUBNET

variable "create_fss" {
  type = bool
  default = true
}

variable "fss_subnet_cidr" {
  default = "10.1.162.0/24"
}

variable "fss_subnet_dns_label" {
  default = "fss"
}

variable "fss_subnet_name" {
  default = "fss"
}

variable "create_gateways" {
  type = bool
  default = true
}

variable "service_gateway_id" {
  default = null
}

variable "nat_gateway_id" {
  default = null
}

variable "create_internet_gateway" {
  type = bool
  default = true
}

#CONTROL PLANE EXTERNAL CONNECTION

variable "cp_external_nat" {
  type = bool
  default = true
}

variable "allow_external_cp_traffic" {
  type = bool
  default = true
}

variable "cp_egress_cidr" {
  default = "0.0.0.0/0"
}

# DRG

variable "enable_drg" {
  type = bool
  default = false
}

variable "create_drg" {
  type = bool
  default = true
}

variable "drg_id" {
  default = null
}

variable "drg_name" {
  default = null
}

variable "create_drg_attachment" {
  type = bool
  default = true
}

variable "peer_vcns" {
  type = list(string)
  default = []
}

