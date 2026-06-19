output "container_instance_dynamic_group_id" {
  description = "OCID of the container instance dynamic group"
  value       = var.create_dynamic_groups ? oci_identity_dynamic_group.container_instance_dg[0].id : ""
}

output "management_agent_dynamic_group_id" {
  description = "OCID of the management agent dynamic group"
  value       = try(oci_identity_dynamic_group.management_agent_dg[0].id, "")
}

output "container_logging_policy_id" {
  description = "OCID of the container logging policy"
  value       = try(oci_identity_policy.container_logging_policy[0].id, "")
}

output "mgmt_agent_metrics_policy_id" {
  description = "OCID of the management agent metrics policy"
  value       = try(oci_identity_policy.mgmt_agent_metrics_policy[0].id, "")
}
