
resource "oci_devops_deploy_pipeline" "deploy_pipeline_helm" {
  project_id = oci_devops_project.devops_project.id
  display_name = "helm-install-pipeline"
  description = "Deployment pipeline to install Helm charts on a OKE cluster"
}



resource oci_devops_deploy_stage deploy_helm_stage {
  are_hooks_enabled = true
  deploy_pipeline_id = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
    }
  }
  deploy_stage_type = "OKE_HELM_CHART_DEPLOYMENT"
  description  = "Install the Helm chart on the specified OKE environment"
  display_name = "deploy-helm"
  helm_chart_deploy_artifact_id = oci_devops_deploy_artifact.argo_chart.id
  max_history = 5
  namespace = "$${namespace}"
  oke_cluster_deploy_environment_id = var.is_oke_cluster_private ? oci_devops_deploy_environment.oke_environment_private.0.id : oci_devops_deploy_environment.oke_environment_public.0.id
  purpose      = "EXECUTE_HELM_UPGRADE"
  release_name = "$${artifact}"
  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }
  should_skip_crds = false
  timeout_in_seconds = "300"
  values_artifact_ids = [oci_devops_deploy_artifact.argo_chart_values.id]
}