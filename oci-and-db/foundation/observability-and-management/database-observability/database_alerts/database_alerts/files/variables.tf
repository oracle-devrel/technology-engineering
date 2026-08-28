variable "compartment_id" {
  description = "Optional OCI compartment OCID. When set, all Database Management managed databases in this compartment are selected and tags is ignored."
  type        = string
  default     = null
  nullable    = true
}

variable "tags" {
  description = "Optional free-form tags used to select Database Management managed databases when compartment_id is null. All tags must match."
  type        = map(string)
  default     = {}
}

variable "email_endpoint" {
  description = "Email endpoint for the OCI Notifications subscription. OCI sends a confirmation email before delivery becomes active."
  type        = string
  default     = "test@acme.com"
}

variable "freeform_tags" {
  description = "Tags applied to the Terraform-managed notification topics and alarms."
  type        = map(string)
  default     = {}
}

variable "enable_full_management_alarms" {
  description = "Create FRA and Data Guard alarms, which require Database Management Full Management metrics."
  type        = bool
  default     = true
}

variable "enable_ops_insights_reports" {
  description = "Create a weekly Ops Insights News Report only in compartments containing at least one selected database with an ENABLED Database Insight."
  type        = bool
  default     = true
}

variable "enable_log_analytics_alerts" {
  description = "Create Log Analytics ingest-time rules and OCI Monitoring alarms only for selected databases with an active Log Analytics entity and one or more associated sources."
  type        = bool
  default     = true
}

variable "cpu_critical_percent" {
  description = "CPU utilization threshold for the critical alarm."
  type        = number
  default     = 90
}

variable "storage_critical_percent" {
  description = "Database storage utilization threshold for the critical alarm."
  type        = number
  default     = 90
}

variable "fra_critical_percent" {
  description = "Flash Recovery Area utilization threshold for the critical alarm."
  type        = number
  default     = 90
}

variable "dataguard_apply_lag_critical_seconds" {
  description = "Data Guard apply-lag threshold. Set this to the customer-approved RPO in seconds."
  type        = number
  default     = 900
}
