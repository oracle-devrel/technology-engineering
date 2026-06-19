output "container_instance_id" {
  description = "OCID of the container instance"
  value       = oci_container_instances_container_instance.main.id
}

output "container_instance_name" {
  description = "Name of the container instance"
  value       = oci_container_instances_container_instance.main.display_name
}

output "container_instance_state" {
  description = "State of the container instance"
  value       = data.oci_container_instances_container_instance.main.state
}

output "container_instance_private_ip" {
  description = "Private IP address of the container instance"
  value       = data.oci_container_instances_container_instance.main.vnics[0].private_ip
}

output "container_instance_public_ip" {
  description = "Public IP address of the container instance"
  value       = data.oci_core_vnic.container_vnic.public_ip_address
}

output "container_ids" {
  description = "Container IDs within the instance"
  value       = [for container in data.oci_container_instances_container_instance.main.containers : container.container_id]
}

output "availability_domain" {
  description = "Availability domain of the container instance"
  value       = oci_container_instances_container_instance.main.availability_domain
}

output "time_created" {
  description = "Time the container instance was created"
  value       = oci_container_instances_container_instance.main.time_created
}
