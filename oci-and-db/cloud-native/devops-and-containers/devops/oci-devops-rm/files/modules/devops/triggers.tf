resource "oci_devops_trigger" "application_source_commit" {
  for_each = local.components_by_name

  display_name   = "${each.value.name}-main-commit"
  description    = "Runs ${each.value.name} delivery when the source repository changes"
  project_id     = oci_devops_project.devops_project.id
  trigger_source = "DEVOPS_CODE_REPOSITORY"

  actions {
    build_pipeline_id = oci_devops_build_pipeline.application_delivery[each.key].id
    type              = "TRIGGER_BUILD_PIPELINE"

    filter {
      trigger_source = "DEVOPS_CODE_REPOSITORY"
      events         = ["PUSH"]

      include {
        head_ref = "main"
      }
    }
  }

  actions {
    build_pipeline_id = oci_devops_build_pipeline.application_pull_request[each.key].id
    type              = "TRIGGER_BUILD_PIPELINE"

    filter {
      trigger_source = "DEVOPS_CODE_REPOSITORY"
      events         = ["PULL_REQUEST_CREATED", "PULL_REQUEST_UPDATED"]

      include {
        base_ref = "main"
      }
    }
  }

  repository_id = oci_devops_repository.application_source[each.key].id

  depends_on = [
    oci_devops_build_pipeline_stage.trigger_dev_deployment,
    oci_devops_build_pipeline_stage.application_pull_request
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_trigger" "application_chart_commit" {
  for_each = local.applications_by_name

  display_name   = "${each.value.name}-chart-main-commit"
  description    = "Routes chart repository changes to component or application baseline lifecycles"
  project_id     = oci_devops_project.devops_project.id
  trigger_source = "DEVOPS_CODE_REPOSITORY"

  dynamic "actions" {
    for_each = {
      for component in each.value.components : component.name => local.components_by_name[component.name]
    }

    content {
      build_pipeline_id = oci_devops_build_pipeline.application_delivery[actions.key].id
      type              = "TRIGGER_BUILD_PIPELINE"

      filter {
        trigger_source = "DEVOPS_CODE_REPOSITORY"
        events         = ["PUSH"]

        include {
          head_ref = "main"

          file_filter {
            file_paths = ["${actions.value.chart_path}/**"]
          }
        }
      }
    }
  }

  actions {
    build_pipeline_id = oci_devops_build_pipeline.application_baseline_package[each.key].id
    type              = "TRIGGER_BUILD_PIPELINE"

    filter {
      trigger_source = "DEVOPS_CODE_REPOSITORY"
      events         = ["PUSH"]

      include {
        head_ref = "main"

        file_filter {
          file_paths = ["${each.value.chart_path}/**"]
        }
      }

      exclude {
        file_filter {
          file_paths = ["${each.value.chart_path}/charts/**"]
        }
      }
    }
  }

  repository_id = oci_devops_repository.application_chart[each.key].id

  depends_on = [
    oci_devops_build_pipeline_stage.trigger_application_baseline_deployment,
    oci_devops_build_pipeline_stage.trigger_dev_deployment
  ]

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_trigger" "cluster_admin_commit" {
  for_each = local.cluster_admin_singleton

  display_name = "cluster-admin-main-commit"
  description  = "Validates and deploys changed cluster administration targets"
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "source-trigger"
  })
  project_id     = oci_devops_project.devops_project.id
  trigger_source = "DEVOPS_CODE_REPOSITORY"
  repository_id  = oci_devops_repository.cluster_admin[each.key].id

  actions {
    build_pipeline_id = oci_devops_build_pipeline.cluster_admin_build[each.key].id
    type              = "TRIGGER_BUILD_PIPELINE"

    filter {
      trigger_source = "DEVOPS_CODE_REPOSITORY"
      events         = ["PUSH"]

      include {
        head_ref = "main"
      }
    }
  }

  actions {
    build_pipeline_id = oci_devops_build_pipeline.cluster_admin_pr[each.key].id
    type              = "TRIGGER_BUILD_PIPELINE"

    filter {
      trigger_source = "DEVOPS_CODE_REPOSITORY"
      events         = ["PULL_REQUEST_CREATED", "PULL_REQUEST_UPDATED"]

      include {
        base_ref = "main"
      }
    }
  }

  depends_on = [
    oci_devops_build_pipeline_stage.cluster_admin_build,
    oci_devops_build_pipeline_stage.cluster_admin_pr
  ]

  lifecycle {
    ignore_changes = all
  }
}
