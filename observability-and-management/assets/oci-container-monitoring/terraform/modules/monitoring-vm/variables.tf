variable "compartment_ocid" {
  description = "Compartment OCID"
  type        = string
}

variable "availability_domain" {
  description = "Availability Domain"
  type        = string
}

variable "subnet_ocid" {
  description = "Subnet OCID"
  type        = string
}

variable "resource_prefix" {
  description = "Resource name prefix"
  type        = string
}

variable "instance_shape" {
  description = "Instance shape"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs"
  type        = number
  default     = 1
}

variable "instance_memory_gb" {
  description = "Memory in GB"
  type        = number
  default     = 8
}

variable "os_version" {
  description = "Oracle Linux version"
  type        = string
  default     = "8"
}

variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "assign_public_ip" {
  description = "Assign public IP to instance"
  type        = bool
  default     = true
}

variable "nsg_ids" {
  description = "List of NSG OCIDs"
  type        = list(string)
  default     = []
}

variable "mgmt_agent_install_key" {
  description = "Management Agent install key"
  type        = string
  sensitive   = true
}

variable "region" {
  description = "OCI Region"
  type        = string
}

variable "grafana_admin_password" {
  description = "Grafana admin password"
  type        = string
  sensitive   = true
  default     = ""
}

variable "prometheus_port" {
  description = "Prometheus port"
  type        = number
  default     = 9090
}

variable "prometheus_targets" {
  description = "List of Prometheus scrape targets (legacy, for backward compatibility)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_cadvisor" {
  description = "List of cAdvisor scrape targets (port 8080)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_node_exporter" {
  description = "List of Node Exporter scrape targets (port 9100)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_nginx_exporter" {
  description = "List of Nginx Exporter scrape targets (port 9113)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_redis_exporter" {
  description = "List of Redis Exporter scrape targets (port 9121)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_postgres_exporter" {
  description = "List of PostgreSQL Exporter scrape targets (port 9187)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_mysql_exporter" {
  description = "List of MySQL Exporter scrape targets (port 9104)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_blackbox_exporter" {
  description = "List of Blackbox Exporter scrape targets (port 9115)"
  type        = list(string)
  default     = []
}

variable "prometheus_targets_app" {
  description = "List of application-level Prometheus scrape targets"
  type        = list(string)
  default     = []
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
