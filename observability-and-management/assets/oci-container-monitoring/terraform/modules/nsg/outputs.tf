output "container_nsg_id" {
  description = "Container NSG ID"
  value       = var.create_container_nsg ? oci_core_network_security_group.container_nsg[0].id : null
}

output "monitoring_vm_nsg_id" {
  description = "Monitoring VM NSG ID"
  value       = var.create_vm_nsg ? oci_core_network_security_group.monitoring_vm_nsg[0].id : null
}

output "container_nsg_name" {
  description = "Container NSG name"
  value       = var.create_container_nsg ? oci_core_network_security_group.container_nsg[0].display_name : null
}

output "monitoring_vm_nsg_name" {
  description = "Monitoring VM NSG name"
  value       = var.create_vm_nsg ? oci_core_network_security_group.monitoring_vm_nsg[0].display_name : null
}
