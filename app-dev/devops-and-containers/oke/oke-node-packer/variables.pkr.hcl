variable "availability_domain" {
  type    = string
}

variable "base_image_ocid" {
  type    = string
}

variable "compartment_ocid" {
  type    = string
}

variable "image_prefix" {
  type    = string
}

variable "shape" {
  type    = string
}

variable "ocpus" {
  type    = number
  default = 1
}

variable "memory_in_gbs" {
  type    = number
  default = 8
}

variable "subnet_ocid" {
  type    = string
}

variable "ssh_username" {
  type    = string
  default = "opc"
}

variable "region" {
  type    = string
}

variable "skip_create_image" {
  type    = bool
  default = false
}
