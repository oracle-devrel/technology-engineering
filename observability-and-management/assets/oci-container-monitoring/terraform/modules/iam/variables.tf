variable "tenancy_ocid" {
  description = "Tenancy OCID"
  type        = string
}

variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "resource_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "container-monitoring"
}

variable "create_dynamic_groups" {
  description = "Create dynamic groups"
  type        = bool
  default     = true
}

variable "create_policies" {
  description = "Create IAM policies"
  type        = bool
  default     = true
}

variable "enable_management_agent" {
  description = "Enable management agent policies"
  type        = bool
  default     = true
}

variable "enable_alarms" {
  description = "Enable alarm policies"
  type        = bool
  default     = false
}

variable "existing_container_dg_name" {
  description = "Name of existing container instance dynamic group"
  type        = string
  default     = ""
}

variable "existing_agent_dg_name" {
  description = "Name of existing management agent dynamic group"
  type        = string
  default     = ""
}

variable "freeform_tags" {
  description = "Freeform tags"
  type        = map(string)
  default     = {}
}
