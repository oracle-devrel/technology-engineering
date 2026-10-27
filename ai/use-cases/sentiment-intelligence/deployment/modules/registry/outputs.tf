output "backend_repo_path" {
  description = "Full path of the backend container repository"
  value       = oci_artifacts_container_repository.backend.display_name
}

output "frontend_repo_path" {
  description = "Full path of the frontend container repository"
  value       = oci_artifacts_container_repository.frontend.display_name
}
