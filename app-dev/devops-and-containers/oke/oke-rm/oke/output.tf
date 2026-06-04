output "cluster_id" {
  value = module.oke.cluster_id
}

output "worker_pools" {
  value = module.oke.worker_pools
}

output "oidc_discovery_endpoint" {
  value = module.oke.cluster_oidc_discovery_endpoint
}

output "policy_statements" {
  value = var.enable_policies ? concat(local.compute_statements, local.network_statements, local.storage_statements, local.tag_statements, local.iam_statements) : []
}