variable "compartment_ocid" {
  type = string
}

variable "repo_name" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}
