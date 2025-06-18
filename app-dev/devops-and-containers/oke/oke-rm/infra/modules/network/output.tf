output "vcn_id" {
  value = local.vcn_id
}

# SUBNETS

output "cp_subnet_id" {
  value = local.create_cp_subnet ? oci_core_subnet.oke_cp_subnet.0.id : null
}

output "pod_subnet_id" {
  value = local.create_pod_subnet ? oci_core_subnet.pods_subnet.0.id : null
}

output "worker_subnet_id" {
  value = local.create_worker_subnet ? oci_core_subnet.worker_subnet.0.id : null
}

output "service_subnet_id" {
  value = local.create_service_subnet ? oci_core_subnet.service_subnet.0.id : null
}

output "bastion_subnet_id" {
  value = var.create_bastion_subnet ? oci_core_subnet.bastion_subnet[0].id : null
}

# NSG

output "cp_nsg_id" {
  value = oci_core_network_security_group.cp_nsg.id
}

output "pod_nsg_id" {
  value = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : null
}

output "worker_nsg_id" {
  value = oci_core_network_security_group.worker_nsg.id
}

output "lb_nsg_id" {
  value = oci_core_network_security_group.oke_lb_nsg.id
}
