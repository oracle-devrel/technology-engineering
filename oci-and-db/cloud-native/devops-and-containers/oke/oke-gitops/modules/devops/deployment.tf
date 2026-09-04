resource "oci_devops_deploy_pipeline" "deploy_pipeline_helm" {
  project_id   = oci_devops_project.devops_project.id
  display_name = "install-gitops-agent"
  description  = "Internal deployment target used only by bootstrap-gitops-agent to prepare OKE and install the selected GitOps agent"

  deploy_pipeline_parameters {
    items {
      name          = "chart_version"
      default_value = "CHANGE_ME"
      description   = "Exact chart version already mirrored to OCIR; bootstrap-gitops-agent supplies this automatically"
    }
    items {
      name          = "chart_name"
      default_value = var.gitops_agent == "fluxcd" ? "flux-operator" : "argo-cd"
      description   = "Helm release name"
    }
    items {
      name          = "namespace"
      default_value = local.gitops_namespace
      description   = "Namespace where the GitOps agent is installed"
    }
    items {
      name          = "target_cluster_id"
      default_value = var.oke_cluster_id
      description   = "OKE cluster OCID prepared by this pipeline; set explicitly when reusing the artifacts for another Flux member"
    }
    items {
      name          = "region_key"
      default_value = local.region_key
      description   = "OCIR region key used to resolve mirrored GitOps images"
    }
    items {
      name          = "tenancy_namespace"
      default_value = local.namespace
      description   = "Object Storage tenancy namespace used by OCIR"
    }
    items {
      name          = "repo_prefix"
      default_value = var.ocir_repo_path_prefix
      description   = "OCIR repository prefix containing mirrored GitOps artifacts"
    }
    items {
      name          = "deployment_nonce"
      default_value = "manual"
      description   = "Unique bootstrap run identifier that prevents OCI DevOps from skipping a same-version Helm reconciliation"
    }
    items {
      name          = "git_read_credentials_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "OCI Vault JSON credential secret for read-only Git access, passed by bootstrap-gitops-agent"
    }
    items {
      name          = "registry_pull_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "OCI Vault JSON credential secret for read-only OCIR access, passed by bootstrap-gitops-agent"
    }
    items {
      name          = "auth_token_secret_ocid"
      default_value = "CHANGE_ME"
      description   = "Deprecated legacy raw-token Vault secret, passed by bootstrap-gitops-agent"
    }
  }
}

resource "oci_devops_deploy_stage" "prepare_gitops_bootstrap" {
  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.gitops_bootstrap_prepare.id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
  deploy_stage_type               = "SHELL"
  description                     = "Create the GitOps namespace and credentials before the Helm installation"
  display_name                    = "prepare-gitops-agent"
  timeout_in_seconds              = 900

  container_config {
    container_config_type = "CONTAINER_INSTANCE_CONFIG"
    compartment_id        = var.compartment_id
    shape_name            = "CI.Standard.E4.Flex"

    shape_config {
      ocpus         = 1
      memory_in_gbs = 1
    }

    network_channel {
      network_channel_type = "SERVICE_VNIC_CHANNEL"
      subnet_id            = var.oke_worker_subnet_id
      nsg_ids              = local.oke_worker_nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
    }
  }
}

resource "oci_devops_deploy_stage" "deploy_helm_stage" {
  are_hooks_enabled  = true
  deploy_pipeline_id = oci_devops_deploy_pipeline.deploy_pipeline_helm.id
  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.prepare_gitops_bootstrap.id
    }
  }
  deploy_stage_type                 = "OKE_HELM_CHART_DEPLOYMENT"
  description                       = "Install the Helm chart on the specified OKE environment"
  display_name                      = "deploy-helm"
  helm_chart_deploy_artifact_id     = var.gitops_agent == "fluxcd" ? oci_devops_deploy_artifact.flux_operator_chart.0.id : oci_devops_deploy_artifact.argocd_operator_chart.0.id
  max_history                       = 5
  namespace                         = "$${namespace}"
  oke_cluster_deploy_environment_id = oci_devops_deploy_environment.oke_environment.id
  purpose                           = "EXECUTE_HELM_UPGRADE"
  release_name                      = "$${chart_name}"
  is_force_enabled                  = true
  set_string {
    items {
      name  = "bootstrapNonce"
      value = "$${deployment_nonce}"
    }
  }
  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }
  should_skip_crds    = false
  timeout_in_seconds  = "300"
  values_artifact_ids = var.gitops_agent == "fluxcd" ? [oci_devops_deploy_artifact.flux_operator_values.0.id] : [oci_devops_deploy_artifact.argocd_operator_values.0.id]
}
