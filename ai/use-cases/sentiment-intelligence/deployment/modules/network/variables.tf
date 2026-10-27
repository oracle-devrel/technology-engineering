variable "compartment_ocid" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "vcn_cidr_block" {
  type = string
}

variable "public_subnet_cidr" {
  type = string
}

variable "private_subnet_cidr" {
  type = string
}

variable "db_subnet_cidr" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}
