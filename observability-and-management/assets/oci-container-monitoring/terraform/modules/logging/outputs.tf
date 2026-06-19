output "log_group_id" {
  description = "OCID of the log group"
  value       = local.log_group_id
}

output "log_group_name" {
  description = "Name of the log group"
  value       = var.log_group_name
}

output "application_log_id" {
  description = "OCID of the application log"
  value       = oci_logging_log.container_application_log.id
}

output "system_log_id" {
  description = "OCID of the system log"
  value       = oci_logging_log.container_system_log.id
}

output "audit_log_id" {
  description = "OCID of the audit log"
  value       = var.enable_audit_logs ? oci_logging_log.container_audit_log[0].id : null
}

output "prometheus_metrics_log_id" {
  description = "OCID of the Prometheus metrics log"
  value       = var.enable_management_agent ? oci_logging_log.prometheus_metrics_log[0].id : null
}
