resource "oci_devops_deploy_artifact" "application_chart" {
  for_each = local.applications_by_name

  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "HELM_CHART"
  description                = "Packaged ${each.value.name} application Helm chart in OCIR"
  display_name               = "${each.value.name}-chart"
  freeform_tags = {
    application = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    chart_url                   = each.value.ocir_chart
    deploy_artifact_source_type = "HELM_CHART"
    deploy_artifact_version     = "$${chart_version}"

    helm_verification_key_source {
      verification_key_source_type = "NONE"
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "component_chart" {
  for_each = local.components_by_name

  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "HELM_CHART"
  description                = "Packaged ${each.value.name} Helm chart in OCIR"
  display_name               = "${each.value.name}-chart"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    chart_url                   = each.value.ocir_chart
    deploy_artifact_source_type = "HELM_CHART"
    deploy_artifact_version     = "$${component_chart_version}"

    helm_verification_key_source {
      verification_key_source_type = "NONE"
    }
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "application_baseline_values" {
  for_each = local.applications_by_name

  argument_substitution_mode = "SUBSTITUTE_PLACEHOLDERS"
  deploy_artifact_type       = "GENERIC_FILE"
  description                = "${local.baseline_cluster_name} cluster baseline values for the ${each.value.name} Helm release"
  display_name               = "${each.value.name}-values-${local.baseline_cluster_name}"
  freeform_tags = {
    application = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content       = base64encode(templatefile("${path.root}/templates/application-baseline-values.yaml.tpl", {}))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "application_prod_values" {
  for_each = local.applications_by_name

  argument_substitution_mode = "SUBSTITUTE_PLACEHOLDERS"
  deploy_artifact_type       = "GENERIC_FILE"
  description                = "prod cluster baseline values for the ${each.value.name} Helm release"
  display_name               = "${each.value.name}-values-prod"
  freeform_tags = {
    application = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content       = base64encode(templatefile("${path.root}/templates/application-baseline-values.yaml.tpl", {}))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "component_values" {
  for_each = local.component_environment_pairs

  argument_substitution_mode = "SUBSTITUTE_PLACEHOLDERS"
  deploy_artifact_type       = "GENERIC_FILE"
  description                = "${each.value.environment} values for the ${each.value.name} Helm release"
  display_name               = "${each.value.name}-values-${each.value.environment}"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/component-values.yaml.tpl", {
      application_chart_name = each.value.application_name
      component_name         = each.value.name
      environment            = each.value.environment
      image_tag_parameter    = "image_tag"
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "component_prod_values" {
  for_each = local.components_by_name

  argument_substitution_mode = "SUBSTITUTE_PLACEHOLDERS"
  deploy_artifact_type       = "GENERIC_FILE"
  description                = "prod values for the ${each.value.name} Helm release"
  display_name               = "${each.value.name}-values-prod"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/component-values.yaml.tpl", {
      application_chart_name = each.value.application_name
      component_name         = each.value.name
      environment            = "prod"
      image_tag_parameter    = "image_tag"
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "application_bootstrap_command_spec" {
  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Initializes an application namespace and OCIR image pull secret on noprod or prod"
  display_name               = "application-bootstrap-command-spec"
  freeform_tags = {
    purpose = "application-bootstrap"
    role    = "namespace-initialization"
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/application-bootstrap-command-spec.yaml.tpl", {
      kube_endpoint         = local.kube_endpoint
      noprod_oke_cluster_id = var.oke_cluster_id
      prod_oke_cluster_id   = local.prod_oke_cluster_id
      region                = var.region
      region_key            = local.region_key
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "component_verify_deployment_command_spec" {
  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Reports a completed production component Helm release status"
  display_name               = "component-prod-status-command-spec"
  freeform_tags = {
    purpose = "component-delivery"
    role    = "deployment-status"
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/verify-component-production-command-spec.yaml.tpl", {
      kube_endpoint       = local.kube_endpoint
      prod_oke_cluster_id = local.prod_oke_cluster_id
      region              = var.region
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "promote_release_image_command_spec" {
  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Promotes an approved component RC image tag to the final release tag"
  display_name               = "component-promote-release-image-command-spec"
  freeform_tags = {
    purpose = "component-delivery"
    role    = "release-image-promotion"
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/promote-release-image-command-spec.yaml.tpl", {
      region = var.region
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_deploy_artifact" "tag_release_commit_command_spec" {
  argument_substitution_mode = "NONE"
  deploy_artifact_type       = "COMMAND_SPEC"
  description                = "Tags a released component source commit after production deployment"
  display_name               = "component-tag-release-commit-command-spec"
  freeform_tags = {
    purpose = "component-delivery"
    role    = "release-commit-tagging"
  }
  project_id = oci_devops_project.devops_project.id

  deploy_artifact_source {
    base64encoded_content = base64encode(templatefile("${path.root}/templates/tag-release-commit-command-spec.yaml.tpl", {
      region = var.region
    }))
    deploy_artifact_source_type = "INLINE"
  }

  lifecycle {
    ignore_changes = all
  }
}
