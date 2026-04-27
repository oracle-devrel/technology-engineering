resource "oci_devops_build_pipeline" "mirror_gitops_agent" {
  project_id   = oci_devops_project.devops_project.id
  display_name = "mirror-gitops-agent"
  description  = "Pipeline to mirror the public Helm Chart of the GitOps Agent into OCIR"
}

resource "oci_devops_build_pipeline_stage" "mirror_gitops_agent_stage" {
  build_pipeline_id         = oci_devops_build_pipeline.mirror_gitops_agent.id
  build_pipeline_stage_type = "BUILD"
  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.mirror_gitops_agent.id
    }
  }
  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "pipelines"
      repository_id   = oci_devops_repository.devops_pipelines_repo_flux.0.id
      repository_url  = oci_devops_repository.devops_pipelines_repo_flux.0.http_url
    }
  }
  build_spec_file                    = "mirror_flux_operator.yaml"
  display_name                       = "Mirror GitOps Agent Helm Chart"
  description                        = "Stage to import a public Helm Chart into the tenancy Oracle Container Registry"
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
}

resource "oci_devops_build_pipeline_stage" "trigger_helm_deploy" {
  build_pipeline_id         = oci_devops_build_pipeline.mirror_gitops_agent.id
  build_pipeline_stage_type = "TRIGGER_DEPLOYMENT_PIPELINE"
  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline_stage.mirror_gitops_agent_stage.id
    }
  }
  deploy_pipeline_id             = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
  description                    = "Trigger CD pipeline to deploy on OKE"
  display_name                   = "Trigger Helm Deployment pipeline"
  is_pass_all_parameters_enabled = true
}