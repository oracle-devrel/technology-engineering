variable "region" {}
variable "compartment_id" {}
variable "bastion_subnet_id" {}
variable "vcn_name" {}


variable "bastion_cidr_block_allow_list" {
  type = list(string)
}