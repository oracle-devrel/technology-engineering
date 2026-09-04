output "vcn_id" {
  description = "OCID of the VCN used by the OKE infrastructure."
  value       = module.network.vcn_id
}

output "cp_subnet_id" {
  description = "OCID of the OKE control plane subnet, when created by this stack."
  value       = module.network.cp_subnet_id
}

output "worker_subnet_id" {
  description = "OCID of the OKE worker subnet, when created by this stack."
  value       = module.network.worker_subnet_id
}

output "pod_subnet_id" {
  description = "OCID of the OKE pod subnet, when created for VCN-native pod networking."
  value       = module.network.pod_subnet_id
}

output "external_lb_subnet_id" {
  description = "OCID of the public load balancer subnet, when created by this stack."
  value       = module.network.external_lb_subnet_id
}

output "internal_lb_subnet_id" {
  description = "OCID of the private load balancer subnet, when created by this stack."
  value       = module.network.internal_lb_subnet_id
}

output "bastion_subnet_id" {
  description = "OCID of the bastion subnet, when created by this stack."
  value       = module.network.bastion_subnet_id
}

output "db_subnet_id" {
  description = "OCID of the database subnet, when created by this stack."
  value       = module.network.db_subnet_id
}

output "msg_subnet_id" {
  description = "OCID of the messaging subnet, when created by this stack."
  value       = module.network.msg_subnet_id
}

output "cp_nsg_id" {
  description = "OCID of the network security group for the OKE control plane."
  value       = module.network.cp_nsg_id
}

output "worker_nsg_id" {
  description = "OCID of the network security group for OKE worker nodes."
  value       = module.network.worker_nsg_id
}

output "pod_nsg_id" {
  description = "OCID of the network security group for OKE pods when using VCN-native pod networking."
  value       = module.network.pod_nsg_id
}

output "lb_nsg_id" {
  description = "OCID of the network security group for OKE load balancers."
  value       = module.network.lb_nsg_id
}

output "database_nsg_ids" {
  description = "Database service names mapped to their database-side NSG OCIDs."
  value       = module.network.database_nsg_ids
}

output "database_client_nsg_ids" {
  description = "Database service names mapped to their dedicated pod- or worker-side NSG OCIDs. Empty when separate database NSGs are disabled."
  value       = module.network.database_client_nsg_ids
}

output "streaming_nsg_id" {
  description = "OCID of the OCI Streaming NSG, when created by this stack."
  value       = module.network.streaming_nsg_id
}
