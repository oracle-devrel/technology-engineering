output "devops_project_id" {
  description = "OCID of the OCI DevOps project."
  value       = oci_devops_project.devops_project.id
}

output "pipelines_repository_url" {
  description = "HTTPS URL of the shared pipelines repository."
  value       = oci_devops_repository.platform_pipelines.http_url
}

output "cluster_admin_repository_url" {
  description = "HTTPS URL of the cluster administration repository."
  value       = try(oci_devops_repository.cluster_admin["enabled"].http_url, null)
}

output "cluster_admin_values_repository_id" {
  description = "OCID of the Generic Artifact repository containing immutable cluster tool values and deployment plans."
  value       = try(oci_artifacts_repository.cluster_admin_values["enabled"].id, null)
}

output "cluster_admin_build_pipeline_ids" {
  description = "Shared cluster administration build pipeline OCIDs."
  value = var.enable_cluster_admin ? {
    build  = oci_devops_build_pipeline.cluster_admin_build["enabled"].id
    mirror = oci_devops_build_pipeline.cluster_admin_mirror["enabled"].id
    pr     = oci_devops_build_pipeline.cluster_admin_pr["enabled"].id
  } : {}
}

output "cluster_admin_deploy_pipeline_ids" {
  description = "Cluster administration deployment and decommission pipeline OCIDs."
  value = merge(
    { for name, pipeline in oci_devops_deploy_pipeline.cluster_admin : name => pipeline.id },
    { for name, pipeline in oci_devops_deploy_pipeline.cluster_admin_decommission : "${name}-decommission" => pipeline.id }
  )
}

output "component_source_repository_urls" {
  description = "Component name to OCI DevOps source repository URL."
  value = {
    for name, repo in oci_devops_repository.application_source : name => repo.http_url
  }
}

output "application_chart_repository_urls" {
  description = "Application name to OCI DevOps chart repository URL."
  value = {
    for name, repo in oci_devops_repository.application_chart : name => repo.http_url
  }
}

output "component_build_pipeline_ids" {
  description = "Component name to build pipeline OCID."
  value = {
    for name, pipeline in oci_devops_build_pipeline.application_delivery : name => pipeline.id
  }
}

output "component_pr_pipeline_ids" {
  description = "Component name to pull request validation pipeline OCID."
  value = {
    for name, pipeline in oci_devops_build_pipeline.application_pull_request : name => pipeline.id
  }
}

output "component_release_build_pipeline_ids" {
  description = "Component name to release build pipeline OCID."
  value = {
    for name, pipeline in oci_devops_build_pipeline.release_application : name => pipeline.id
  }
}

output "application_package_pipeline_ids" {
  description = "Application name to baseline chart package pipeline OCID."
  value = {
    for name, pipeline in oci_devops_build_pipeline.application_baseline_package : name => pipeline.id
  }
}

output "application_deploy_pipeline_ids" {
  description = "Application name to baseline deployment pipeline OCID."
  value = {
    for name, pipeline in oci_devops_deploy_pipeline.deploy_application : name => pipeline.id
  }
}

output "application_bootstrap_pipeline_ids" {
  description = "Application name to parallel noprod/prod namespace bootstrap deployment pipeline OCID."
  value = {
    for name, pipeline in oci_devops_deploy_pipeline.application_bootstrap : name => pipeline.id
  }
}

output "component_deploy_pipeline_ids" {
  description = "Component and environment to deployment pipeline OCID."
  value = {
    for key, pipeline in oci_devops_deploy_pipeline.deploy_component : key => pipeline.id
  }
}

output "oke_noprod_deploy_environment_id" {
  description = "OCID of the pre-production OKE deployment environment."
  value       = local.oke_environment_id
}

output "oke_prod_deploy_environment_id" {
  description = "OCID of the production OKE deployment environment."
  value       = local.prod_oke_environment_id
}

output "application_components" {
  description = "Application name to component names."
  value = {
    for name, application in local.applications_by_name : name => [
      for component in application.components : component.name
    ]
  }
}

output "application_namespaces" {
  description = "Application name to pre-production Kubernetes namespace."
  value = {
    for name, application in local.applications_by_name : name => application.namespace
  }
}

output "application_prod_namespaces" {
  description = "Application name to production Kubernetes namespace."
  value = {
    for name, application in local.applications_by_name : name => application.prod_namespace
  }
}

output "application_ocir_charts" {
  description = "Application name to umbrella Helm chart OCI URL."
  value = {
    for name, application in local.applications_by_name : name => application.ocir_chart
  }
}

output "component_ocir_charts" {
  description = "Component name to Helm chart OCI URL."
  value = {
    for name, component in local.components_by_name : name => component.ocir_chart
  }
}

output "component_image_repositories" {
  description = "Component name to OCIR image repository."
  value = {
    for name, component in local.components_by_name : name => component.image_repository
  }
}
