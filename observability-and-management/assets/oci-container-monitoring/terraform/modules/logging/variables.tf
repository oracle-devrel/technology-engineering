variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "log_group_name" {
  description = "Log group display name"
  type        = string
}

variable "container_instance_id" {
  description = "Container Instance OCID (optional, defaults to empty string)"
  type        = string
  default     = ""
}

variable "enable_logging" {
  description = "Enable logging"
  type        = bool
  default     = true
}

variable "enable_audit_logs" {
  description = "Enable audit logs"
  type        = bool
  default     = true
}

variable "enable_management_agent" {
  description = "Enable management agent logging"
  type        = bool
  default     = true
}

variable "enable_log_analytics" {
  description = "Enable Log Analytics integration"
  type        = bool
  default     = false
}

variable "log_retention_days" {
  description = "Log retention in days"
  type        = number
  default     = 30

  validation {
    condition     = contains([30, 60, 90, 120, 180, 365], var.log_retention_days)
    error_message = "Log retention must be one of: 30, 60, 90, 120, 180, 365 days"
  }
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
