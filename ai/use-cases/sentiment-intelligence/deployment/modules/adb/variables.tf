variable "compartment_ocid" {
  type = string
}

variable "resource_prefix" {
  type = string
}

variable "db_display_name" {
  type = string
}

variable "db_name" {
  type = string
}

variable "admin_password" {
  type      = string
  sensitive = true
}

variable "cpu_core_count" {
  type = number
}

variable "data_storage_size_in_gb" {
  type = number
}

variable "db_workload" {
  type = string
}

variable "is_free_tier" {
  type = bool
}

variable "license_model" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "nsg_id" {
  type = string
}

variable "freeform_tags" {
  type    = map(string)
  default = {}
}
