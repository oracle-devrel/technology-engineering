resource "oci_devops_deploy_pipeline" "deploy_application" {
  for_each = local.applications_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-deploy"
  description  = "Promotes the ${each.value.name} namespace baseline through noprod approval and production"
  freeform_tags = {
    application = each.value.name
  }

  deploy_pipeline_parameters {
    items {
      name          = "chart_version"
      default_value = each.value.chart_version
      description   = "Application baseline chart version to deploy"
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_pipeline" "deploy_component" {
  for_each = local.component_environment_pairs

  project_id   = oci_devops_project.devops_project.id
  display_name = each.value.environment == "staging" ? "${each.value.name}-release" : "${each.value.name}-${each.value.environment}-deploy"
  description  = each.value.environment == "staging" ? "Promotes ${each.value.name} through staging approval and production" : "Deploys the ${each.value.environment} ${each.value.name} Helm release from OCIR"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }

  deploy_pipeline_parameters {
    items {
      name          = "component_chart_version"
      default_value = each.value.chart_version
      description   = "${each.value.name} chart version to deploy"
    }
    items {
      name          = "image_repository"
      default_value = each.value.image_repository
      description   = "Image repository for ${each.value.name}"
    }
    items {
      name          = "image_tag"
      default_value = ""
      description   = each.value.environment == "staging" ? "Release candidate image tag to deploy, for example 1.0.0-rc.1" : "Image tag for ${each.value.name}; set explicitly for manual deployments"
    }

    items {
      name          = "source_repository_id"
      default_value = oci_devops_repository.application_source[each.value.name].id
      description   = "OCI DevOps source repository to tag after production succeeds"
    }

  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_pipeline" "application_bootstrap" {
  for_each = local.applications_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-bootstrap"
  description  = "Initializes the ${each.value.name} namespace and OCIR pull secret on noprod and prod"
  freeform_tags = {
    application = each.value.name
    role        = "application-bootstrap"
  }

  deploy_pipeline_parameters {
    items {
      name          = "registry_username"
      default_value = null
      description   = "OCIR pull username, for example tenancy-namespace/user"
    }
    items {
      name          = "pull_password_secret_ocid"
      default_value = null
      description   = "Vault secret OCID containing the OCIR pull password or auth token"
    }
    items {
      name          = "secret_name"
      default_value = var.namespace_init_secret_name
      description   = "Kubernetes docker-registry secret name"
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "application_bootstrap_namespace" {
  for_each = local.application_bootstrap_targets

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.application_bootstrap_command_spec.id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.application_bootstrap[each.value.application_name].id
  deploy_stage_type               = "SHELL"
  description                     = "Create the ${each.value.namespace} namespace and OCIR pull secret on ${each.value.cluster_name}"
  display_name                    = "${each.value.application_name}-${each.value.cluster_name}-bootstrap"
  timeout_in_seconds              = 600
  freeform_tags = {
    application = each.value.application_name
    cluster     = each.value.cluster_name
    namespace   = each.value.namespace
    role        = "namespace-bootstrap"
  }

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
      subnet_id            = each.value.subnet_id
      nsg_ids              = each.value.nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.application_bootstrap[each.value.application_name].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "deploy_application" {
  for_each = local.applications_by_name

  are_hooks_enabled                 = true
  deploy_pipeline_id                = oci_devops_deploy_pipeline.deploy_application[each.key].id
  deploy_stage_type                 = "OKE_HELM_CHART_DEPLOYMENT"
  description                       = "Install or upgrade the ${local.baseline_cluster_name} ${each.value.name} baseline Helm chart from OCIR"
  display_name                      = "${each.value.name}-${local.baseline_cluster_name}-deploy"
  helm_chart_deploy_artifact_id     = oci_devops_deploy_artifact.application_chart[each.key].id
  max_history                       = 5
  namespace                         = each.value.namespace
  oke_cluster_deploy_environment_id = local.oke_environment_id
  purpose                           = "EXECUTE_HELM_UPGRADE"
  release_name                      = "${each.value.name}-${local.baseline_cluster_name}"
  should_skip_crds                  = false
  timeout_in_seconds                = 600
  values_artifact_ids               = [oci_devops_deploy_artifact.application_baseline_values[each.key].id]

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.deploy_application[each.key].id
    }
  }

  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "approve_application_prod_baseline" {
  for_each = local.applications_by_name

  approval_policy {
    approval_policy_type         = "COUNT_BASED_APPROVAL"
    number_of_approvals_required = 1
  }

  deploy_pipeline_id = oci_devops_deploy_pipeline.deploy_application[each.key].id
  deploy_stage_type  = "MANUAL_APPROVAL"
  description        = "Approve promotion of ${each.value.name} namespace baseline from noprod to production"
  display_name       = "${each.value.name}-prod-approve"

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.deploy_application[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "deploy_application_prod" {
  for_each = local.applications_by_name

  are_hooks_enabled                 = true
  deploy_pipeline_id                = oci_devops_deploy_pipeline.deploy_application[each.key].id
  deploy_stage_type                 = "OKE_HELM_CHART_DEPLOYMENT"
  description                       = "Install or upgrade the prod ${each.value.name} baseline Helm chart from OCIR"
  display_name                      = "${each.value.name}-prod-deploy"
  helm_chart_deploy_artifact_id     = oci_devops_deploy_artifact.application_chart[each.key].id
  max_history                       = 5
  namespace                         = each.value.prod_namespace
  oke_cluster_deploy_environment_id = local.prod_oke_environment_id
  purpose                           = "EXECUTE_HELM_UPGRADE"
  release_name                      = each.value.name
  should_skip_crds                  = false
  timeout_in_seconds                = 600
  values_artifact_ids               = [oci_devops_deploy_artifact.application_prod_values[each.key].id]

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.approve_application_prod_baseline[each.key].id
    }
  }

  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "deploy_component" {
  for_each = local.component_environment_pairs

  are_hooks_enabled                 = true
  deploy_pipeline_id                = oci_devops_deploy_pipeline.deploy_component[each.key].id
  deploy_stage_type                 = "OKE_HELM_CHART_DEPLOYMENT"
  description                       = "Install or upgrade the ${each.value.environment} ${each.value.name} Helm chart from OCIR"
  display_name                      = "${each.value.name}-${each.value.environment}-deploy"
  helm_chart_deploy_artifact_id     = oci_devops_deploy_artifact.component_chart[each.value.name].id
  max_history                       = 5
  namespace                         = each.value.application_namespace
  oke_cluster_deploy_environment_id = local.oke_environment_id
  purpose                           = "EXECUTE_HELM_UPGRADE"
  release_name                      = "${each.value.name}-${each.value.environment}"
  should_skip_crds                  = false
  timeout_in_seconds                = 600
  values_artifact_ids               = [oci_devops_deploy_artifact.component_values[each.key].id]

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_pipeline.deploy_component[each.key].id
    }
  }

  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "approve_component_prod_release" {
  for_each = local.components_by_name

  approval_policy {
    approval_policy_type         = "COUNT_BASED_APPROVAL"
    number_of_approvals_required = 1
  }

  deploy_pipeline_id = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  deploy_stage_type  = "MANUAL_APPROVAL"
  description        = "Approve promotion of ${each.value.name} from staging to production"
  display_name       = "${each.value.name}-prod-approve"

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.deploy_component["${each.key}:staging"].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "promote_component_release_image" {
  for_each = local.components_by_name

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.promote_release_image_command_spec.id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  deploy_stage_type               = "SHELL"
  description                     = "Retag the approved RC image as the final release image"
  display_name                    = "${each.value.name}-release-image-promote"
  timeout_in_seconds              = 600

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
      subnet_id            = local.prod_oke_worker_subnet_id
      nsg_ids              = local.prod_oke_worker_nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.approve_component_prod_release[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "deploy_component_prod" {
  for_each = local.components_by_name

  are_hooks_enabled                 = true
  deploy_pipeline_id                = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  deploy_stage_type                 = "OKE_HELM_CHART_DEPLOYMENT"
  description                       = "Install or upgrade the prod ${each.value.name} Helm chart from OCIR"
  display_name                      = "${each.value.name}-prod-deploy"
  helm_chart_deploy_artifact_id     = oci_devops_deploy_artifact.component_chart[each.key].id
  max_history                       = 5
  namespace                         = each.value.application_prod_namespace
  oke_cluster_deploy_environment_id = local.prod_oke_environment_id
  purpose                           = "EXECUTE_HELM_UPGRADE"
  release_name                      = each.value.name
  should_skip_crds                  = false
  timeout_in_seconds                = 600
  values_artifact_ids               = [oci_devops_deploy_artifact.component_prod_values[each.key].id]

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.promote_component_release_image[each.key].id
    }
  }

  rollback_policy {
    policy_type = "AUTOMATED_STAGE_ROLLBACK_POLICY"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "verify_component_prod" {
  for_each = local.components_by_name

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.component_verify_deployment_command_spec.id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  deploy_stage_type               = "SHELL"
  description                     = "Report the completed production Helm release status"
  display_name                    = "${each.value.name}-prod-status"
  timeout_in_seconds              = 600
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
    environment = "prod"
    namespace   = each.value.application_prod_namespace
    release     = each.value.name
    role        = "deployment-status"
  }

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
      subnet_id            = local.prod_oke_worker_subnet_id
      nsg_ids              = local.prod_oke_worker_nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.tag_component_release_commit[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_stage" "tag_component_release_commit" {
  for_each = local.components_by_name

  command_spec_deploy_artifact_id = oci_devops_deploy_artifact.tag_release_commit_command_spec.id
  deploy_pipeline_id              = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  deploy_stage_type               = "SHELL"
  description                     = "Create the final source Git tag after production deployment succeeds"
  display_name                    = "${each.value.name}-release-commit-tag"
  timeout_in_seconds              = 600

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
      subnet_id            = local.prod_oke_worker_subnet_id
      nsg_ids              = local.prod_oke_worker_nsg_ids
    }
  }

  deploy_stage_predecessor_collection {
    items {
      id = oci_devops_deploy_stage.deploy_component_prod[each.key].id
    }
  }

  lifecycle {
    ignore_changes = all
  }
}
