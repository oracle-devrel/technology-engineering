variable "compartment_ocid" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "vcn_id" {
  type = string
}

variable "public_subnet_id" {
  type = string
}

variable "private_subnet_id" {
  type = string
}

variable "kubernetes_version" {
  type = string
}

variable "node_pool_size" {
  type = number
}

variable "node_shape" {
  type = string
}

variable "node_ocpus" {
  type = number
}

variable "node_memory_in_gbs" {
  type = number
}

variable "node_pool_image_type" {
  type = string
}

variable "availability_domain" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}
