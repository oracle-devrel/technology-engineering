resource "oci_devops_build_pipeline" "mirror_gitops_agent" {
  project_id   = oci_devops_project.devops_project.id
  display_name = "mirror-gitops-agent"
  description  = "Mirror the selected GitOps agent chart and images into OCIR without deploying them"

  build_pipeline_parameters {
    items {
      name          = "chart_version"
      default_value = "LATEST"
      description   = "Exact Helm chart version to mirror, or LATEST to resolve the current upstream version"
    }
  }
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
      repository_id   = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.id : oci_devops_repository.devops_pipelines_repo_argocd.0.id
      repository_url  = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.http_url : oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
    }
  }
  build_spec_file                    = var.gitops_agent == "fluxcd" ? "mirror_flux_operator.yaml" : "mirror_argocd.yaml"
  display_name                       = "Mirror GitOps Agent Helm Chart"
  description                        = "Stage to import a public Helm Chart into the tenancy Oracle Container Registry"
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
}

resource "oci_devops_build_pipeline" "bootstrap_gitops_agent" {
  project_id   = oci_devops_project.devops_project.id
  display_name = "bootstrap-gitops-agent"
  description  = "Mirror and install the selected GitOps agent on the configured OKE cluster"

  build_pipeline_parameters {
    items {
      name          = "chart_version"
      default_value = "LATEST"
      description   = "Exact Helm chart version to mirror and install, or LATEST to resolve the current upstream version"
    }
    items {
      name          = "git_read_credentials_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "OCI Vault secret OCID containing JSON username/password credentials for read-only Git access"
    }
    items {
      name          = "registry_pull_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "OCI Vault secret OCID containing JSON username/password credentials for read-only OCIR access"
    }
    items {
      name          = "auth_token_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "Deprecated legacy OCI Vault secret OCID containing one raw auth token for Git and OCIR"
    }
  }
}

resource "oci_devops_build_pipeline_stage" "bootstrap_gitops_agent_stage" {
  build_pipeline_id         = oci_devops_build_pipeline.bootstrap_gitops_agent.id
  build_pipeline_stage_type = "BUILD"
  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.bootstrap_gitops_agent.id
    }
  }
  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "pipelines"
      repository_id   = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.id : oci_devops_repository.devops_pipelines_repo_argocd.0.id
      repository_url  = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.http_url : oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
    }
  }
  build_spec_file                    = var.gitops_agent == "fluxcd" ? "mirror_flux_operator.yaml" : "mirror_argocd.yaml"
  display_name                       = "Mirror GitOps Agent Helm Chart"
  description                        = "Import the selected public Helm chart and its images into OCIR for bootstrap"
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000
}

resource "oci_devops_build_pipeline_stage" "trigger_helm_deploy" {
  build_pipeline_id         = oci_devops_build_pipeline.bootstrap_gitops_agent.id
  build_pipeline_stage_type = "TRIGGER_DEPLOYMENT_PIPELINE"
  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline_stage.bootstrap_gitops_agent_stage.id
    }
  }
  deploy_pipeline_id             = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
  description                    = "Trigger the GitOps agent installation pipeline on OKE"
  display_name                   = "Trigger GitOps agent installation"
  is_pass_all_parameters_enabled = true
}
