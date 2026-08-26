# =============================================================================
# Outputs
# =============================================================================

# ---------- Networking ----------
output "vcn_id" {
  description = "OCID of the VCN"
  value       = module.network.vcn_id
}

# ---------- OKE ----------
output "oke_cluster_id" {
  description = "OCID of the OKE cluster"
  value       = module.oke.cluster_id
}

output "oke_cluster_name" {
  description = "Name of the OKE cluster"
  value       = module.oke.cluster_name
}

output "oke_cluster_endpoint" {
  description = "OKE Kubernetes API endpoint"
  value       = module.oke.cluster_endpoint
}

output "kubeconfig" {
  description = "Kubeconfig for the OKE cluster"
  value       = module.oke.kubeconfig
  sensitive   = true
}

# ---------- Autonomous Database ----------
output "adb_id" {
  description = "OCID of the Autonomous Database"
  value       = module.adb.adb_id
}

output "adb_connection_string" {
  description = "Connection string for the Autonomous Database"
  value       = module.adb.connection_string
  sensitive   = true
}

output "adb_db_name" {
  description = "Database name"
  value       = module.adb.db_name
}

# ---------- Container Registry ----------
output "ocir_backend_repo" {
  description = "OCIR backend repository path"
  value       = module.registry.backend_repo_path
}

output "ocir_frontend_repo" {
  description = "OCIR frontend repository path"
  value       = module.registry.frontend_repo_path
}

output "ocir_url" {
  description = "Base OCIR URL for pushing images"
  value       = local.ocir_url
}

# ---------- GenAI ----------
output "genai_endpoint" {
  description = "OCI Generative AI endpoint URL"
  value       = local.genai_endpoint
}

output "genai_model_id" {
  description = "OCI Generative AI model ID"
  value       = var.genai_model_id
}

output "select_ai_profile" {
  description = "Select AI profile name expected by the backend"
  value       = var.select_ai_profile
}

# ---------- Application ----------
output "app_namespace" {
  description = "Kubernetes namespace for the application"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "frontend_load_balancer" {
  description = "Public IP of the frontend load balancer (available after deployment)"
  value       = "Run: kubectl get svc frontend-service -n ${kubernetes_namespace.app.metadata[0].name} -o jsonpath='{.status.loadBalancer.ingress[0].ip}'"
}

# ---------- Deployment Commands ----------
output "setup_kubeconfig_command" {
  description = "Command to configure kubectl for the OKE cluster"
  value       = "oci ce cluster create-kubeconfig --cluster-id ${module.oke.cluster_id} --region ${var.region} --token-version 2.0.0 --kube-endpoint PUBLIC_ENDPOINT"
}

output "build_push_images_command" {
  description = "Commands to build and push Docker images"
  value       = <<-EOT
    # Login to OCIR
    docker login ${local.region_key}.ocir.io

    # Build and push backend
    docker build -t ${local.ocir_url}/backend:${var.backend_image_tag} ../backend/
    docker push ${local.ocir_url}/backend:${var.backend_image_tag}

    # Build and push frontend
    docker build -t ${local.ocir_url}/frontend:${var.frontend_image_tag} --build-arg VITE_API_BASE_URL=/api ../frontend/
    docker push ${local.ocir_url}/frontend:${var.frontend_image_tag}
  EOT
}
