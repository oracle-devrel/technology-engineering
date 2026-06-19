# ─────────────────────────────────────────────────────────────
# variables.tf – Input variables for the azurelogs2oci OCI Stack
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
  description = "Name for the inbound Azure stream"
  type        = string
  default     = "azure-inbound-stream"
}

variable "stream_partitions" {
  description = "Number of stream partitions"
  type        = number
  default     = 1
}

variable "stream_retention_in_hours" {
  description = "Stream message retention in hours (24-168)"
  type        = number
  default     = 24
}

# --- Log Analytics ---

variable "log_group_name" {
  description = "Log Analytics log group display name"
  type        = string
  default     = "AzureLogs"
}

variable "log_group_description" {
  description = "Log Analytics log group description"
  type        = string
  default     = "Azure log imports via azurelogs2oci pipeline"
}

variable "log_analytics_namespace" {
  description = "Log Analytics namespace (leave empty for auto-detection)"
  type        = string
  default     = ""
}

# --- Service Connector Hub ---

variable "sch_name" {
  description = "Service Connector Hub display name"
  type        = string
  default     = "Azure-Stream-to-LogAnalytics"
}

variable "sch_description" {
  description = "Service Connector Hub description"
  type        = string
  default     = "Forwards Azure logs from OCI Streaming to Log Analytics"
}

# --- IAM ---

variable "create_iam_policies" {
  description = "Create IAM policies for SCH (set false if policies already exist)"
  type        = bool
  default     = true
}

# --- Compute (future extensibility) ---
# These variables are not used by the current serverless stack but are
# provided so that adding a compute instance later (e.g. a self-hosted
# log forwarder) requires only resource blocks, not new variables.

variable "compute_shape" {
  description = "Compute instance shape for optional future instances (VM.Standard.E5.Flex, VM.Standard.E4.Flex, VM.Standard.A2.Flex, VM.Standard.A1.Flex, VM.Standard3.Flex, VM.Optimized3.Flex)"
  type        = string
  default     = "VM.Standard.E5.Flex"
}

variable "compute_ocpus" {
  description = "Number of OCPUs for flex compute shapes (1-64)"
  type        = number
  default     = 1
}

variable "compute_memory_in_gbs" {
  description = "Memory in GBs for flex compute shapes (1-1024)"
  type        = number
  default     = 16
}

variable "compute_image_id" {
  description = "Custom image OCID for future compute instances (leave empty to use platform images)"
  type        = string
  default     = ""
}
