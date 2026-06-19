variable "tenancy_ocid" {
  description = "Tenancy OCID"
  type        = string
}

variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "container_instance_name" {
  description = "Container instance display name"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "container_shape" {
  description = "Container instance shape"
  type        = string
  default     = "CI.Standard.E4.Flex"

  validation {
    condition     = contains(["CI.Standard.E3.Flex", "CI.Standard.E4.Flex"], var.container_shape)
    error_message = "Shape must be CI.Standard.E3.Flex or CI.Standard.E4.Flex"
  }
}

variable "container_ocpus" {
  description = "Number of OCPUs"
  type        = number
  default     = 1

  validation {
    condition     = var.container_ocpus >= 1 && var.container_ocpus <= 64
    error_message = "OCPUs must be between 1 and 64"
  }
}

variable "container_memory_gb" {
  description = "Memory in GB"
  type        = number
  default     = 4

  validation {
    condition     = var.container_memory_gb >= 1 && var.container_memory_gb <= 1024
    error_message = "Memory must be between 1GB and 1024GB"
  }
}

variable "container_count" {
  description = "Number of container replicas"
  type        = number
  default     = 1
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 80
}

variable "container_env_vars" {
  description = "Container environment variables"
  type        = map(string)
  default     = {}
}

variable "availability_domain" {
  description = "Availability domain number (1, 2, or 3)"
  type        = number
  default     = 1

  validation {
    condition     = var.availability_domain >= 1 && var.availability_domain <= 3
    error_message = "Availability domain must be 1, 2, or 3"
  }
}

variable "subnet_ocid" {
  description = "Subnet OCID"
  type        = string
}

variable "assign_public_ip" {
  description = "Assign public IP"
  type        = bool
  default     = true
}

variable "nsg_ocids" {
  description = "Network Security Group OCIDs"
  type        = list(string)
  default     = []
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/"
}

variable "container_restart_policy" {
  description = "Container restart policy"
  type        = string
  default     = "ALWAYS"

  validation {
    condition     = contains(["ALWAYS", "NEVER", "ON_FAILURE"], var.container_restart_policy)
    error_message = "Restart policy must be ALWAYS, NEVER, or ON_FAILURE"
  }
}

variable "volume_mounts" {
  description = "Volume mounts for containers"
  type = list(object({
    mount_path   = string
    volume_name  = string
    is_read_only = optional(bool, false)
  }))
  default = []
}

variable "volumes" {
  description = "Volumes for container instance"
  type = list(object({
    name        = string
    volume_type = string
    data        = optional(map(string), {})
  }))
  default = []
}

variable "ocir_username" {
  description = "OCIR username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ocir_auth_token" {
  description = "OCIR auth token"
  type        = string
  default     = ""
  sensitive   = true
}

variable "ocir_endpoint" {
  description = "OCIR endpoint"
  type        = string
  default     = ""
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

#######################################
# Management Agent Variables
#######################################
variable "enable_management_agent" {
  description = "Enable Management Agent sidecar container (Legacy - does NOT work in Container Instances)"
  type        = bool
  default     = false
}

variable "enable_prometheus_exporters" {
  description = "Enable Prometheus exporters (cAdvisor + Node Exporter) for container monitoring"
  type        = bool
  default     = true
}

#######################################
# Application-Specific Exporters
#######################################
variable "enable_nginx_exporter" {
  description = "Enable Nginx Exporter for nginx metrics (port 9113)"
  type        = bool
  default     = false
}

variable "enable_redis_exporter" {
  description = "Enable Redis Exporter for redis metrics (port 9121)"
  type        = bool
  default     = false
}

variable "enable_postgres_exporter" {
  description = "Enable PostgreSQL Exporter for postgres metrics (port 9187)"
  type        = bool
  default     = false
}

variable "enable_mysql_exporter" {
  description = "Enable MySQL Exporter for mysql metrics (port 9104)"
  type        = bool
  default     = false
}

variable "enable_blackbox_exporter" {
  description = "Enable Blackbox Exporter for endpoint probing (port 9115)"
  type        = bool
  default     = false
}

variable "mgmt_agent_install_key" {
  description = "Management Agent install key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "region" {
  description = "OCI Region"
  type        = string
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

variable "prometheus_metrics_port" {
  description = "Port where Prometheus metrics are exposed"
  type        = number
  default     = 9090
}

variable "prometheus_metrics_path" {
  description = "Path where Prometheus metrics are exposed"
  type        = string
  default     = "/metrics"
}

variable "metrics_namespace" {
  description = "OCI Monitoring metrics namespace"
  type        = string
  default     = "container_monitoring"
}

#######################################
# Sidecar Container Images
#######################################
variable "enable_management_agent_sidecar" {
  description = "Enable Management Agent as sidecar container (new architecture with custom image)"
  type        = bool
  default     = false
}

variable "enable_prometheus_sidecar" {
  description = "Enable Prometheus as sidecar container for metrics aggregation"
  type        = bool
  default     = false
}

variable "enable_shared_volumes" {
  description = "Enable shared volumes for sidecar communication (/metrics, /logs)"
  type        = bool
  default     = false
}

variable "mgmt_agent_sidecar_image" {
  description = "Management Agent sidecar container image URL (custom image from OCIR)"
  type        = string
  default     = ""
}

variable "prometheus_sidecar_image" {
  description = "Prometheus sidecar container image URL (custom image from OCIR)"
  type        = string
  default     = ""
}

variable "mgmt_agent_sidecar_memory_gb" {
  description = "Memory allocation for Management Agent sidecar in GB"
  type        = number
  default     = 1.0
}

variable "mgmt_agent_sidecar_ocpus" {
  description = "OCPU allocation for Management Agent sidecar"
  type        = number
  default     = 0.25
}

variable "prometheus_sidecar_memory_gb" {
  description = "Memory allocation for Prometheus sidecar in GB"
  type        = number
  default     = 1.0
}

variable "prometheus_sidecar_ocpus" {
  description = "OCPU allocation for Prometheus sidecar"
  type        = number
  default     = 0.25
}

variable "enable_log_forwarder_sidecar" {
  description = "Enable Log Forwarder as sidecar container for forwarding logs to OCI Logging"
  type        = bool
  default     = false
}

variable "log_forwarder_sidecar_image" {
  description = "Log Forwarder sidecar container image URL (custom image from OCIR)"
  type        = string
  default     = ""
}

variable "log_forwarder_sidecar_memory_gb" {
  description = "Memory allocation for Log Forwarder sidecar in GB"
  type        = number
  default     = 0.5
}

variable "log_forwarder_sidecar_ocpus" {
  description = "OCPU allocation for Log Forwarder sidecar"
  type        = number
  default     = 0.125
}

variable "log_ocid" {
  description = "OCI Logging Log OCID for log forwarder to send logs to. Required when enable_log_forwarder_sidecar is true, otherwise logs will be collected but silently discarded."
  type        = string
  default     = ""
}

variable "enable_grafana_sidecar" {
  description = "Enable Grafana as sidecar container for metrics visualization and OCI Logs querying"
  type        = bool
  default     = false
}

variable "grafana_sidecar_image" {
  description = "Grafana sidecar container image URL (custom image with OCI Logs plugin from OCIR)"
  type        = string
  default     = ""
}

variable "grafana_sidecar_memory_gb" {
  description = "Memory allocation for Grafana sidecar in GB"
  type        = number
  default     = 0.5
}

variable "grafana_sidecar_ocpus" {
  description = "OCPU allocation for Grafana sidecar"
  type        = number
  default     = 0.25
}

variable "grafana_admin_user" {
  description = "Grafana admin username"
  type        = string
  default     = "admin"
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  default     = "admin"
  sensitive   = true
}
