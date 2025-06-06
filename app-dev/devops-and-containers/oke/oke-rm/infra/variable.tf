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
  default = "vcn-spoke-1"
}

variable "vcn_cidr_blocks" {
  type = list(string)
  default = ["10.1.0.0/16"]
}

variable "vcn_dns_label" {
  default = "spoke1"
}

# CP SUBNET

variable "create_cp_subnet" {
  type = bool
  default = true
}

variable "cp_subnet_cidr" {
  default = "10.1.0.0/29"
}

variable "cp_subnet_dns_label" {
  default = "cp"
}

variable "cp_subnet_name" {
  default = "cp-subnet"
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
  default = "10.1.8.0/21"
}

variable "worker_subnet_dns_label" {
  default = "worker"
}

variable "worker_subnet_name" {
  default = "worker-subnet"
}

# POD SUBNET

variable "create_pod_subnet" {
  type = bool
  default = true
}

variable "pod_subnet_cidr" {
  default = "10.1.128.0/18"
}

variable "pod_subnet_dns_label" {
  default = "pod"
}

variable "pod_subnet_name" {
  default = "pod-subnet"
}

# SERVICE SUBNET

variable "create_service_subnet" {
  type = bool
  default = true
}

variable "service_subnet_cidr" {
  default = "10.1.0.32/27"
}

variable "service_subnet_private" {
  type = bool
  default = true
}

variable "service_subnet_dns_label" {
  default = "service"
}

variable "service_subnet_name" {
  default = "service-subnet"
}

# BASTION SUBNET

variable "create_bastion_subnet" {
  type = bool
  default = true
}

variable "bastion_subnet_cidr" {
  default = "10.1.0.8/29"
}

variable "bastion_subnet_private" {
  type = bool
  default = false
}

variable "bastion_subnet_dns_label" {
  default = "bastion"
}

variable "bastion_subnet_name" {
  default = "bastion-subnet"
}

# FSS SUBNET

variable "create_fss" {
  type = bool
  default = false
}

variable "fss_subnet_cidr" {
  default = "10.1.0.64/26"
}

variable "fss_subnet_dns_label" {
  default = "fss"
}

variable "fss_subnet_name" {
  default = "fss-subnet"
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

# BASTION MODULE

variable "create_bastion" {
  type = bool
  default = false
}

variable "bastion_compartment_id" {
  default = null
}

variable "bastion_cidr_block_allow_list" {
  type = list(string)
  default = ["0.0.0.0/0"]
}

