output "devops_project_id" {
  description = "OCID of the OCI DevOps project."
  value       = module.devops.devops_project_id
}

output "pipelines_repository_url" {
  description = "HTTPS URL of the shared pipelines repository."
  value       = module.devops.pipelines_repository_url
}

output "cluster_admin_repository_url" {
  description = "HTTPS URL of the cluster administration repository."
  value       = module.devops.cluster_admin_repository_url
}

output "cluster_admin_values_repository_id" {
  description = "OCID of the Generic Artifact repository containing immutable cluster tool values."
  value       = module.devops.cluster_admin_values_repository_id
}

output "cluster_admin_build_pipeline_ids" {
  description = "Shared cluster administration build pipeline OCIDs."
  value       = module.devops.cluster_admin_build_pipeline_ids
}

output "cluster_admin_deploy_pipeline_ids" {
  description = "Cluster name to cluster administration DAG deployment pipeline OCID."
  value       = module.devops.cluster_admin_deploy_pipeline_ids
}

output "component_source_repository_urls" {
  description = "Component name to OCI DevOps source repository URL."
  value       = module.devops.component_source_repository_urls
}

output "application_chart_repository_urls" {
  description = "Application name to OCI DevOps chart repository URL."
  value       = module.devops.application_chart_repository_urls
}

output "component_build_pipeline_ids" {
  description = "Component name to build pipeline OCID."
  value       = module.devops.component_build_pipeline_ids
}

output "component_pr_pipeline_ids" {
  description = "Component name to pull request validation pipeline OCID."
  value       = module.devops.component_pr_pipeline_ids
}

output "component_release_build_pipeline_ids" {
  description = "Component name to release build pipeline OCID."
  value       = module.devops.component_release_build_pipeline_ids
}

output "application_package_pipeline_ids" {
  description = "Application name to baseline chart package pipeline OCID."
  value       = module.devops.application_package_pipeline_ids
}

output "application_deploy_pipeline_ids" {
  description = "Application name to baseline deployment pipeline OCID."
  value       = module.devops.application_deploy_pipeline_ids
}

output "application_bootstrap_pipeline_ids" {
  description = "Application name to parallel noprod/prod namespace bootstrap deployment pipeline OCID."
  value       = module.devops.application_bootstrap_pipeline_ids
}

output "component_deploy_pipeline_ids" {
  description = "Component and environment to deployment pipeline OCID."
  value       = module.devops.component_deploy_pipeline_ids
}

output "oke_noprod_deploy_environment_id" {
  description = "OCID of the pre-production OKE deployment environment."
  value       = module.devops.oke_noprod_deploy_environment_id
}

output "oke_prod_deploy_environment_id" {
  description = "OCID of the production OKE deployment environment."
  value       = module.devops.oke_prod_deploy_environment_id
}

output "application_components" {
  description = "Application name to component names."
  value       = module.devops.application_components
}

output "application_namespaces" {
  description = "Application name to pre-production Kubernetes namespace."
  value       = module.devops.application_namespaces
}

output "application_prod_namespaces" {
  description = "Application name to production Kubernetes namespace."
  value       = module.devops.application_prod_namespaces
}

output "application_ocir_charts" {
  description = "Application name to umbrella Helm chart OCI URL."
  value       = module.devops.application_ocir_charts
}

output "component_ocir_charts" {
  description = "Component name to Helm chart OCI URL."
  value       = module.devops.component_ocir_charts
}

output "component_image_repositories" {
  description = "Component name to OCIR image repository."
  value       = module.devops.component_image_repositories
}

output "estimated_devops_resources" {
  description = "Estimated generated OCI DevOps resource counts for topology and service-limit review."
  value       = local.estimated_devops_resources
}

output "next_steps" {
  description = "Suggested workflow after the stack is applied."
  value = format(
    "%sBootstrap application namespaces and pull secrets with: %s. Deploy application baselines with: %s. Develop components through pull requests and build pipelines: %s. Promote releases with: %s.",
    var.enable_cluster_admin ? "Open cluster-admin to manage cluster baselines and tools. " : "",
    join(", ", sort([for name in keys(module.devops.application_bootstrap_pipeline_ids) : "${name}-bootstrap"])),
    join(", ", sort([for name in keys(module.devops.application_deploy_pipeline_ids) : "${name}-deploy"])),
    join(", ", sort(keys(module.devops.component_build_pipeline_ids))),
    join(", ", sort([for name in keys(module.devops.component_release_build_pipeline_ids) : "${name}-release-build"]))
  )
}
