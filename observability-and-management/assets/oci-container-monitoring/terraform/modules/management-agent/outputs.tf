output "install_key_id" {
  description = "Management Agent install key OCID"
  value       = oci_management_agent_management_agent_install_key.main.id
}

output "install_key" {
  description = "Management Agent install key"
  value       = oci_management_agent_management_agent_install_key.main.key
  sensitive   = true
}

output "install_key_expires" {
  description = "Install key expiration time"
  value       = oci_management_agent_management_agent_install_key.main.time_expires
}

output "agent_config" {
  description = "Complete agent configuration"
  value       = local.agent_config
  sensitive   = true
}

output "install_script_path" {
  description = "Path to agent installation script"
  value       = local_file.agent_install_script.filename
}

output "prometheus_config_path" {
  description = "Path to Prometheus configuration file"
  value       = local_file.prometheus_config.filename
}

output "service_discovery_config_path" {
  description = "Path to service discovery configuration"
  value       = local_file.service_discovery_config.filename
}

output "agent_config_json_path" {
  description = "Path to agent configuration JSON"
  value       = local_file.agent_config_json.filename
}
