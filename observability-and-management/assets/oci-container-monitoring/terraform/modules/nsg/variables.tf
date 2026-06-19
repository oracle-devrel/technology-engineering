variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "vcn_ocid" {
  description = "VCN OCID"
  type        = string
}

variable "resource_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "allowed_cidr" {
  description = "CIDR block allowed to access resources (e.g., your IP/32)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "create_container_nsg" {
  description = "Create NSG for container instances"
  type        = bool
  default     = true
}

variable "create_vm_nsg" {
  description = "Create NSG for monitoring VM"
  type        = bool
  default     = false
}

variable "freeform_tags" {
  description = "Freeform tags"
  type        = map(string)
  default     = {}
}

variable "defined_tags" {
  description = "Defined tags"
  type        = map(string)
  default     = {}
}
