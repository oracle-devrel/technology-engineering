resource "oci_devops_build_pipeline" "application_delivery" {
  for_each = local.components_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-build"
  description  = "Builds ${each.value.name} images when source changes and packages the component chart when chart files change"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "application_delivery" {
  for_each = local.components_by_name

  build_pipeline_id         = oci_devops_build_pipeline.application_delivery[each.key].id
  build_pipeline_stage_type = "BUILD"
  display_name              = "${title(replace(each.value.name, "-", " "))} Build"
  description               = "Conditionally builds the component image and packages the component chart"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }
  build_spec_file                    = each.value.build_spec_path
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.application_delivery[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "pipelines"
      repository_id   = oci_devops_repository.platform_pipelines.id
      repository_url  = oci_devops_repository.platform_pipelines.http_url
    }
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = each.value.name
      repository_id   = oci_devops_repository.application_source[each.key].id
      repository_url  = oci_devops_repository.application_source[each.key].http_url
    }
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "application-chart"
      repository_id   = oci_devops_repository.application_chart[each.value.application_name].id
      repository_url  = oci_devops_repository.application_chart[each.value.application_name].http_url
    }
  }

  depends_on = [
    null_resource.seed_platform_entities,
    null_resource.seed_application_source,
    null_resource.seed_application_chart_components
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "trigger_dev_deployment" {
  for_each = local.components_by_name

  build_pipeline_id              = oci_devops_build_pipeline.application_delivery[each.key].id
  build_pipeline_stage_type      = "TRIGGER_DEPLOYMENT_PIPELINE"
  deploy_pipeline_id             = oci_devops_deploy_pipeline.deploy_component["${each.key}:dev"].id
  display_name                   = "${title(replace(each.value.name, "-", " "))} Dev Deploy"
  description                    = "Triggers the dev component deployment after a successful build"
  is_pass_all_parameters_enabled = true

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline_stage.application_delivery[each.key].id
    }
  }

  depends_on = [
    oci_devops_deploy_stage.deploy_component
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline" "application_baseline_package" {
  for_each = local.applications_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-package"
  description  = "Packages the ${each.value.name} application baseline chart and deploys it to the noprod cluster"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "application_baseline_package" {
  for_each = local.applications_by_name

  build_pipeline_id         = oci_devops_build_pipeline.application_baseline_package[each.key].id
  build_pipeline_stage_type = "BUILD"
  display_name              = "${title(replace(each.value.name, "-", " "))} Package"
  description               = "Packages the ${each.value.name} umbrella baseline chart"
  freeform_tags = {
    application = each.value.name
  }
  build_spec_file                    = "${each.value.name}-package-pipeline.yaml"
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.application_baseline_package[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "pipelines"
      repository_id   = oci_devops_repository.platform_pipelines.id
      repository_url  = oci_devops_repository.platform_pipelines.http_url
    }
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "application-chart"
      repository_id   = oci_devops_repository.application_chart[each.key].id
      repository_url  = oci_devops_repository.application_chart[each.key].http_url
    }
  }

  depends_on = [
    null_resource.seed_platform_entities,
    null_resource.seed_application_chart_baseline
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "trigger_application_baseline_deployment" {
  for_each = local.applications_by_name

  build_pipeline_id              = oci_devops_build_pipeline.application_baseline_package[each.key].id
  build_pipeline_stage_type      = "TRIGGER_DEPLOYMENT_PIPELINE"
  deploy_pipeline_id             = oci_devops_deploy_pipeline.deploy_application[each.key].id
  display_name                   = "${title(replace(each.value.name, "-", " "))} Noprod Deploy"
  description                    = "Triggers the noprod application baseline deployment after packaging"
  is_pass_all_parameters_enabled = true

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline_stage.application_baseline_package[each.key].id
    }
  }

  depends_on = [
    oci_devops_deploy_stage.deploy_application
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline" "application_pull_request" {
  for_each = local.components_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-pr"
  description  = "Runs component-owned pull request validation for ${each.value.name}"

  lifecycle {
    # OCI rejects some updates to parameterless pipeline containers.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "application_pull_request" {
  for_each = local.components_by_name

  build_pipeline_id         = oci_devops_build_pipeline.application_pull_request[each.key].id
  build_pipeline_stage_type = "BUILD"
  display_name              = "${title(replace(each.value.name, "-", " "))} Pull Request"
  description               = "Runs the component-owned pull request build spec"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }
  build_spec_file                    = ".oci-devops/pull-request-pipeline.yaml"
  primary_build_source               = each.value.name
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.application_pull_request[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = each.value.name
      repository_id   = oci_devops_repository.application_source[each.key].id
      repository_url  = oci_devops_repository.application_source[each.key].http_url
    }
  }

  depends_on = [
    null_resource.seed_application_source
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline" "release_application" {
  for_each = local.components_by_name

  project_id   = oci_devops_project.devops_project.id
  display_name = "${each.value.name}-release-build"
  description  = "Creates a source Git tag and retags the matching SHA image"
  freeform_tags = {
    application = each.value.application_name
    component   = each.value.name
  }

  build_pipeline_parameters {
    items {
      name          = "release_tag"
      default_value = "CHANGE_ME"
      description   = "Strict SemVer release candidate tag, for example 0.1.0-rc.1"
    }
    items {
      name          = "commit_id"
      default_value = "CHANGE_ME"
      description   = "Optional full commit SHA to release. When unset, the current source main commit is used."
    }
  }

  lifecycle {
    # OCI pipeline parameters are intentionally preserved as a complete contract.
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "release_application" {
  for_each = local.components_by_name

  build_pipeline_id                  = oci_devops_build_pipeline.release_application[each.key].id
  build_pipeline_stage_type          = "BUILD"
  display_name                       = "${title(replace(each.value.name, "-", " "))} Release"
  description                        = "Creates the source Git tag and retags the SHA image"
  build_spec_file                    = "${each.value.name}-release-pipeline.yaml"
  primary_build_source               = "pipelines"
  image                              = "OL8_X86_64_STANDARD_10"
  stage_execution_timeout_in_seconds = 36000

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline.release_application[each.key].id
    }
  }

  build_source_collection {
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "pipelines"
      repository_id   = oci_devops_repository.platform_pipelines.id
      repository_url  = oci_devops_repository.platform_pipelines.http_url
    }
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = each.value.name
      repository_id   = oci_devops_repository.application_source[each.key].id
      repository_url  = oci_devops_repository.application_source[each.key].http_url
    }
    items {
      connection_type = "DEVOPS_CODE_REPOSITORY"
      branch          = "main"
      name            = "application-chart"
      repository_id   = oci_devops_repository.application_chart[each.value.application_name].id
      repository_url  = oci_devops_repository.application_chart[each.value.application_name].http_url
    }
  }

  depends_on = [
    null_resource.seed_platform_entities,
    null_resource.seed_application_source,
    null_resource.seed_application_chart_components
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_build_pipeline_stage" "trigger_staging_deployment" {
  for_each = local.components_by_name

  build_pipeline_id              = oci_devops_build_pipeline.release_application[each.key].id
  build_pipeline_stage_type      = "TRIGGER_DEPLOYMENT_PIPELINE"
  deploy_pipeline_id             = oci_devops_deploy_pipeline.deploy_component["${each.key}:staging"].id
  display_name                   = "${title(replace(each.value.name, "-", " "))} Release Pipeline Trigger"
  description                    = "Triggers the component release deployment pipeline after a successful release build"
  is_pass_all_parameters_enabled = true

  build_pipeline_stage_predecessor_collection {
    items {
      id = oci_devops_build_pipeline_stage.release_application[each.key].id
    }
  }

  depends_on = [
    oci_devops_deploy_stage.deploy_component
  ]

  lifecycle {
    ignore_changes = all
  }
}
