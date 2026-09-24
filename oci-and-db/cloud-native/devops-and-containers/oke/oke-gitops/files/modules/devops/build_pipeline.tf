resource "oci_devops_build_pipeline" "mirror_gitops_agent" {
  project_id   = local.devops_project_id
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
      # This is the stage-local source alias; the OCI repository name is configurable.
      name           = "pipelines"
      repository_id  = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.id : oci_devops_repository.devops_pipelines_repo_argocd.0.id
      repository_url = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.http_url : oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
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
  project_id   = local.devops_project_id
  display_name = "bootstrap-gitops-agent"
  description  = "Mirror and install the selected GitOps agent on the configured OKE cluster"

  build_pipeline_parameters {
    items {
      name          = "ENFORCE_HELM_DEPLOYMENT"
      default_value = "true"
      description   = "Request Helm execution on every bootstrap deployment, including same-version reinstalls"
    }
    items {
      name          = "chart_version"
      default_value = "LATEST"
      description   = "Exact Helm chart version to mirror and install, or LATEST to resolve the current upstream version"
    }
    items {
      name          = "git_read_credentials_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "Enter the Secret OCID, not JSON. Create the secret in the DevOps project compartment with plaintext JSON (replace all example values): {\"username\":\"example-tenancy/Default/git-reader\",\"password\":\"REPLACE_WITH_GIT_AUTH_TOKEN\"}. Use a dedicated read-only Git user. Password is an OCI auth token, not the console password. Do not base64-encode the JSON in the Console."
    }
    items {
      name          = "registry_pull_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "Enter the Secret OCID, not JSON. Create the secret in the DevOps project compartment with plaintext JSON (replace all example values): {\"username\":\"example-namespace/Default/ocir-reader\",\"password\":\"REPLACE_WITH_OCIR_AUTH_TOKEN\"}. Use a dedicated pull-only OCIR user. Tenancy namespace is the Object Storage namespace, not the tenancy name or OCID. Do not base64-encode the JSON in the Console."
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
      # Keep workspace paths stable when the OCI repository is renamed.
      name           = "pipelines"
      repository_id  = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.id : oci_devops_repository.devops_pipelines_repo_argocd.0.id
      repository_url = var.gitops_agent == "fluxcd" ? oci_devops_repository.devops_pipelines_repo_flux.0.http_url : oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
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
