# --- General Configuration ---

variable "compartment_id" {
  type        = string
  description = "OCID of the compartment where resources will be created"
}

variable "tenancy_ocid" {
  type        = string
  description = "OCID of the tenancy (auto-populated by ORM)"
}

variable "region" {
  type        = string
  description = "OCI region for deployment (auto-populated by ORM)"
}

# --- Log Analytics ---

variable "log_group_name" {
  type        = string
  description = "Name of the Log Analytics log group"
  default     = "soc-detection-test-logs"
}

variable "log_group_description" {
  type        = string
  description = "Description for the Log Analytics log group"
  default     = "Log group for SOC detection rules testing and validation"
}

# --- Streaming ---

variable "stream_pool_id" {
  type        = string
  description = "OCID of an existing stream pool (leave empty to use compartment directly)"
  default     = ""
}

variable "stream_partitions" {
  type        = number
  description = "Number of partitions per stream"
  default     = 1

  validation {
    condition     = var.stream_partitions >= 1 && var.stream_partitions <= 10
    error_message = "Stream partitions must be between 1 and 10."
  }
}

variable "stream_retention_hours" {
  type        = number
  description = "Message retention period in hours"
  default     = 24

  validation {
    condition     = var.stream_retention_hours >= 24 && var.stream_retention_hours <= 168
    error_message = "Retention hours must be between 24 and 168."
  }
}

# --- Provisioning Options ---

variable "deploy_log_sources" {
  type        = bool
  description = "Create custom LA fields, parsers, and log sources"
  default     = true
}

variable "deploy_dashboards" {
  type        = bool
  description = "Deploy SOC detection dashboards and saved searches"
  default     = true
}

variable "deploy_dashboard_cleanup" {
  type        = bool
  description = "Remove existing SOC dashboards before deploying new ones"
  default     = true
}

variable "ingest_test_data" {
  type        = bool
  description = "Upload test attack logs for validation"
  default     = false
}
