output "instance_id" {
  description = "Monitoring VM instance ID"
  value       = oci_core_instance.monitoring_vm.id
}

output "instance_name" {
  description = "Monitoring VM instance name"
  value       = oci_core_instance.monitoring_vm.display_name
}

output "public_ip" {
  description = "Monitoring VM public IP"
  value       = data.oci_core_vnic.monitoring_vm_vnic.public_ip_address
}

output "private_ip" {
  description = "Monitoring VM private IP"
  value       = data.oci_core_vnic.monitoring_vm_vnic.private_ip_address
}

output "grafana_url" {
  description = "Grafana access URL"
  value       = "http://${data.oci_core_vnic.monitoring_vm_vnic.public_ip_address}:3000"
}

output "prometheus_url" {
  description = "Prometheus access URL"
  value       = "http://${data.oci_core_vnic.monitoring_vm_vnic.public_ip_address}:${var.prometheus_port}"
}

output "instance_state" {
  description = "Instance lifecycle state"
  value       = oci_core_instance.monitoring_vm.state
}

output "ssh_command" {
  description = "SSH command to connect to the VM"
  value       = "ssh opc@${data.oci_core_vnic.monitoring_vm_vnic.public_ip_address}"
}
