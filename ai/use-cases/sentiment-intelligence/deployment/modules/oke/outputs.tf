output "cluster_id" {
  description = "OCID of the OKE cluster"
  value       = oci_containerengine_cluster.oke.id
}

output "cluster_name" {
  description = "Name of the OKE cluster"
  value       = oci_containerengine_cluster.oke.name
}

output "kubeconfig" {
  description = "Kubeconfig content for the OKE cluster"
  value       = data.oci_containerengine_cluster_kube_config.kubeconfig.content
  sensitive   = true
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint"
  value       = oci_containerengine_cluster.oke.endpoints[0].public_endpoint
}

output "node_pool_id" {
  description = "OCID of the node pool"
  value       = oci_containerengine_node_pool.pool.id
}
