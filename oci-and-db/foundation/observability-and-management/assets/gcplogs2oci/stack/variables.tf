# ─────────────────────────────────────────────────────────────
# variables.tf – Input variables for the gcplogs2oci OCI Stack
# ─────────────────────────────────────────────────────────────

# --- Required ---

variable "compartment_ocid" {
  description = "Compartment OCID where all resources will be created"
  type        = string
}

variable "region" {
  description = "OCI region (e.g. us-ashburn-1, eu-frankfurt-1)"
  type        = string
}

variable "tenancy_ocid" {
  description = "Tenancy OCID (used for IAM policies)"
  type        = string
}

# --- OCI Streaming ---

variable "stream_pool_name" {
  description = "Display name for the Kafka-compatible Stream Pool"
  type        = string
  default     = "MultiCloud_Log_Pool"
}

variable "stream_name" {
  description = "Name for the inbound stream"
  type        = string
  default     = "gcp-inbound-stream"
}

variable "stream_partitions" {
  description = "Number of stream partitions"
  type        = number
  default     = 1
}

variable "stream_retention_in_hours" {
  description = "Stream message retention in hours (24–168)"
  type        = number
  default     = 24
}

# --- Log Analytics ---

variable "log_group_name" {
  description = "Log Analytics log group display name"
  type        = string
  default     = "GCPLogs"
}

variable "log_group_description" {
  description = "Log Analytics log group description"
  type        = string
  default     = "GCP Cloud Logging imports via gcplogs2oci bridge"
}

variable "log_analytics_namespace" {
  description = "Log Analytics namespace (leave empty for auto-detection)"
  type        = string
  default     = ""
}

# --- Connector Hub ---

variable "sch_name" {
  description = "Connector Hub display name"
  type        = string
  default     = "GCP-Stream-to-LogAnalytics"
}

variable "sch_description" {
  description = "Connector Hub description"
  type        = string
  default     = "Forwards GCP logs from OCI Streaming to Log Analytics using GCP Cloud Logging parser"
}

# --- IAM ---

variable "create_iam_policies" {
  description = "Create IAM policies for SCH (set false if policies already exist)"
  type        = bool
  default     = true
}
