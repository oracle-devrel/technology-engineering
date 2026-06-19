variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "install_key_name" {
  description = "Install key display name"
  type        = string
}

variable "install_key_validity_days" {
  description = "Install key validity in days"
  type        = number
  default     = 365
}

variable "allowed_install_count" {
  description = "Number of allowed agent installations"
  type        = number
  default     = 10
}

variable "is_unlimited_install" {
  description = "Allow unlimited agent installations"
  type        = bool
  default     = false
}

variable "agent_version" {
  description = "Management agent version (empty for latest)"
  type        = string
  default     = ""
}

variable "install_directory" {
  description = "Agent installation directory"
  type        = string
  default     = "/opt/oracle/mgmt_agent"
}

variable "prometheus_scrape_interval" {
  description = "Prometheus scrape interval in seconds"
  type        = number
  default     = 60
}

variable "prometheus_scrape_timeout" {
  description = "Prometheus scrape timeout in seconds"
  type        = number
  default     = 10
}

variable "prometheus_metrics_path" {
  description = "Prometheus metrics path"
  type        = string
  default     = "/metrics"
}

variable "prometheus_metrics_port" {
  description = "Prometheus metrics port"
  type        = number
  default     = 9090
}

variable "prometheus_targets" {
  description = "List of Prometheus scrape targets"
  type        = list(string)
  default     = []
}

variable "prometheus_job_name" {
  description = "Prometheus job name"
  type        = string
  default     = "container-metrics"
}

variable "metrics_namespace" {
  description = "OCI Metrics namespace"
  type        = string
  default     = "container_monitoring"
}

variable "additional_prometheus_labels" {
  description = "Additional labels for Prometheus metrics"
  type        = map(string)
  default     = {}
}

variable "container_instance_id" {
  description = "Container Instance OCID"
  type        = string
}

variable "container_private_ip" {
  description = "Container instance private IP"
  type        = string
}

variable "store_configs_in_object_storage" {
  description = "Store configuration files in Object Storage"
  type        = bool
  default     = false
}

variable "object_storage_namespace" {
  description = "Object Storage namespace"
  type        = string
  default     = ""
}

variable "object_storage_bucket" {
  description = "Object Storage bucket name"
  type        = string
  default     = ""
}

variable "output_directory" {
  description = "Local output directory for configuration files"
  type        = string
  default     = "./output"
}

variable "freeform_tags" {
  description = "Freeform tags"
  type        = map(string)
  default     = {}
}
