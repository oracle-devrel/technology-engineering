output "cluster_id" {
  value = module.oke.cluster_id
}

output "worker_pools" {
  value = module.oke.worker_pools
}

output "oidc_discovery_endpoint" {
  value = module.oke.cluster_oidc_discovery_endpoint
}