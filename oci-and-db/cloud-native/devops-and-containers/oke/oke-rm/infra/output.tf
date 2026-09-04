output "vcn_id" {
  description = "OCID of the VCN used by the OKE infrastructure."
  value       = module.network.vcn_id

  precondition {
    condition     = var.create_vcn || var.vcn_id != null
    error_message = "vcn_id is required when create_vcn is false."
  }

  precondition {
    condition     = !var.enable_drg || var.create_vcn
    error_message = "DRG creation is available only when this stack creates the VCN."
  }

  precondition {
    condition     = !var.create_additional_pod_cidr || length(var.additional_pod_cidr) > 0
    error_message = "additional_pod_cidr must not be empty when create_additional_pod_cidr is true."
  }
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

output "fss_nsg_id" {
  description = "OCID of the network security group to attach to FSS mount targets."
  value       = module.network.fss_nsg_id
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

output "network_resource_suffix" {
  description = "Persistent eight-character UUID suffix appended to generated names and Karpenter network role tag values for this stack."
  value       = module.network.network_resource_suffix
}

output "karpenter_worker_role_tag_value" {
  description = "Unique value of the karpenter-oci/role freeform tag on worker network resources."
  value       = module.network.karpenter_worker_role_tag_value
}

output "karpenter_pod_role_tag_value" {
  description = "Unique value of the karpenter-oci/role freeform tag on pod network resources."
  value       = module.network.karpenter_pod_role_tag_value
}

output "nsg_names" {
  description = "Generated NSG names, including the persistent stack UUID suffix."
  value       = module.network.nsg_names
}
