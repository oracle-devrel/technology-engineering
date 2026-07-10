resource "oci_devops_repository" "platform_pipelines" {
  name            = "pipelines"
  project_id      = oci_devops_project.devops_project.id
  description     = "Reusable pipeline assets for application delivery"
  repository_type = "HOSTED"

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_repository" "application_source" {
  for_each = local.components_by_name

  name            = each.value.name
  project_id      = oci_devops_project.devops_project.id
  description     = "Source code repository for the ${each.value.name} component. Helm chart specifications are intentionally kept separate."
  repository_type = "HOSTED"

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_devops_repository" "application_chart" {
  for_each = local.applications_by_name

  name            = each.value.chart_repository_name
  project_id      = oci_devops_project.devops_project.id
  description     = "Helm chart repository for the ${each.value.name} application. Umbrella and component subchart paths follow separate package and deploy lifecycles."
  repository_type = "HOSTED"

  lifecycle {
    ignore_changes = all
  }
}

resource "local_file" "application_source_env" {
  for_each = local.components_by_name

  filename = "${path.root}/${each.value.repo_path}/.oci-devops/application.env"
  content = templatefile("${path.root}/templates/application-source-env.tpl", {
    component_name = each.value.name
  })
}

resource "local_file" "application_source_pull_request_pipeline" {
  for_each = local.components_by_name

  filename = "${path.root}/${each.value.repo_path}/.oci-devops/pull-request-pipeline.yaml"
  content  = <<-EOT
    version: 0.1
    component: build
    timeoutInSeconds: 1000
    runAs: root
    shell: bash

    steps:
      - type: Command
        name: Run component tests
        failImmediatelyOnError: true
        command: |
          echo "Unit tests succeeded"
  EOT
}

resource "local_file" "application_source_readme" {
  for_each = local.components_by_name

  filename = "${path.root}/${each.value.repo_path}/README.md"
  content = templatefile("${path.root}/templates/application-source-README.md.tpl", {
    application_name      = each.value.application_name
    chart_repository_name = local.applications_by_name[each.value.application_name].chart_repository_name
    component_name        = each.value.name
    devops_project_prefix = local.project_repo_prefix
  })
}

resource "local_file" "application_source_dockerfile" {
  for_each = local.components_by_name

  filename = "${path.root}/${each.value.repo_path}/Dockerfile"
  content = templatefile("${path.root}/templates/application-source-dockerfile.tpl", {
    component_name = each.value.name
  })
}

resource "local_file" "application_chart_readme" {
  for_each = local.applications_by_name

  filename = "${path.root}/${each.value.repo_path}/README.md"
  content = templatefile("${path.root}/templates/application-chart-README.md.tpl", {
    application_name      = each.value.name
    application_path      = each.value.chart_path
    chart_repository_name = each.value.chart_repository_name
    component_name        = join(", ", [for component in each.value.components : component.name])
  })
}

resource "local_file" "application_chart_chart_yaml" {
  for_each = local.applications_by_name

  filename = "${path.root}/${each.value.repo_path}/${each.value.chart_path}/Chart.yaml"
  content = templatefile("${path.root}/templates/application-chart-Chart.yaml.tpl", {
    application_name = each.value.name
    chart_version    = each.value.chart_version
  })
}

resource "local_file" "application_chart_values_yaml" {
  for_each = local.applications_by_name

  filename = "${path.root}/${each.value.repo_path}/${each.value.chart_path}/values.yaml"
  content  = templatefile("${path.root}/templates/application-chart-values.yaml.tpl", {})
}

resource "local_file" "application_chart_helmignore" {
  for_each = local.applications_by_name

  filename = "${path.root}/${each.value.repo_path}/${each.value.chart_path}/.helmignore"
  content  = templatefile("${path.root}/templates/application-chart-helmignore.tpl", {})
}

resource "local_file" "component_chart_chart_yaml" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.applications_by_name[each.value.application_name].repo_path}/${each.value.chart_path}/Chart.yaml"
  content = templatefile("${path.root}/templates/component-chart-Chart.yaml.tpl", {
    chart_version  = each.value.chart_version
    component_name = each.value.name
  })
}

resource "local_file" "component_chart_values_yaml" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.applications_by_name[each.value.application_name].repo_path}/${each.value.chart_path}/values.yaml"
  content = templatefile("${path.root}/templates/component-chart-values.yaml.tpl", {
    application_name = each.value.application_name
    component_name   = each.value.name
  })
}

resource "local_file" "component_chart_deployment_yaml" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.applications_by_name[each.value.application_name].repo_path}/${each.value.chart_path}/templates/deployment.yaml"
  content  = templatefile("${path.root}/templates/component-chart-deployment.yaml.tpl", {})
}

resource "local_file" "component_chart_service_yaml" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.applications_by_name[each.value.application_name].repo_path}/${each.value.chart_path}/templates/service.yaml"
  content  = templatefile("${path.root}/templates/component-chart-service.yaml.tpl", {})
}

resource "local_file" "component_chart_serviceaccount_yaml" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.applications_by_name[each.value.application_name].repo_path}/${each.value.chart_path}/templates/serviceaccount.yaml"
  content  = templatefile("${path.root}/templates/component-chart-serviceaccount.yaml.tpl", {})
}

resource "local_file" "application_delivery_pipeline" {
  for_each = local.generated_component_build_specs

  filename = "${path.root}/${local.platform_repo_path}/${each.value.build_spec_path}"
  content = templatefile("${path.root}/templates/application-delivery-pipeline.yaml.tpl", {
    application_chart_path      = each.value.application_chart_path
    component_chart_repo_prefix = each.value.chart_repo_prefix
    component_image_repo_prefix = each.value.image_repo_prefix
    component_chart_path        = each.value.chart_path
    component_image_repository  = each.value.image_repository
    component_name              = each.value.name
    region                      = var.region
    region_key                  = local.region_key
    repo_compartment_id         = var.compartment_id
    tenancy_namespace           = local.namespace
  })
}

resource "local_file" "custom_application_delivery_pipeline" {
  for_each = local.custom_build_specs_by_path

  filename = "${path.root}/${local.platform_repo_path}/${each.key}"
  content = join("\n", [
    "# Starter generated for components: ${join(", ", each.value.component_names)}.",
    "# This explicit build_spec_path is user-owned after its first commit and is never refreshed by Resource Manager.",
    templatefile("${path.root}/templates/application-delivery-pipeline.yaml.tpl", {
      application_chart_path      = each.value.component.application_chart_path
      component_chart_repo_prefix = each.value.component.chart_repo_prefix
      component_image_repo_prefix = each.value.component.image_repo_prefix
      component_chart_path        = each.value.component.chart_path
      component_image_repository  = each.value.component.image_repository
      component_name              = each.value.component.name
      region                      = var.region
      region_key                  = local.region_key
      repo_compartment_id         = var.compartment_id
      tenancy_namespace           = local.namespace
    })
  ])
}

resource "local_file" "platform_pipelines_readme" {
  filename = "${path.root}/${local.platform_repo_path}/README.md"
  content = templatefile("${path.root}/templates/pipelines-README.md.tpl", {
    application_name = join(", ", keys(local.applications_by_name))
    component_name   = join(", ", keys(local.components_by_name))
  })
}

resource "local_file" "application_baseline_pipeline" {
  for_each = local.applications_by_name

  filename = "${path.root}/${local.platform_repo_path}/${each.value.name}-package-pipeline.yaml"
  content = templatefile("${path.root}/templates/application-baseline-pipeline.yaml.tpl", {
    application_chart_name        = each.value.name
    application_chart_path        = each.value.chart_path
    application_chart_repo_prefix = each.value.chart_repo_prefix
    region                        = var.region
    region_key                    = local.region_key
    repo_compartment_id           = var.compartment_id
    tenancy_namespace             = local.namespace
  })
}

resource "local_file" "helm_chart_pipeline" {
  filename = "${path.root}/${local.platform_repo_path}/helm-chart-pipeline.yaml"
  content = templatefile("${path.root}/templates/helm-chart-pipeline.yaml.tpl", {
    region              = var.region
    region_key          = local.region_key
    repo_compartment_id = var.compartment_id
    tenancy_namespace   = local.namespace
  })
}

resource "local_file" "release_pipeline" {
  for_each = local.components_by_name

  filename = "${path.root}/${local.platform_repo_path}/${each.value.name}-release-pipeline.yaml"
  content = templatefile("${path.root}/templates/release-pipeline.yaml.tpl", {
    application_chart_path      = each.value.chart_path
    component_chart_repo_prefix = each.value.chart_repo_prefix
    component_image_repo_prefix = each.value.image_repo_prefix
    component_image_repository  = each.value.image_repository
    region                      = var.region
    region_key                  = local.region_key
    repo_compartment_id         = var.compartment_id
    tenancy_namespace           = local.namespace
  })
}

resource "null_resource" "seed_platform_shared" {
  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.platform_pipelines.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      # OCI can create a hosted repository with an empty initial commit. Add-only
      # seeds missing starter paths without overwriting adopted repository content.
      SEED_MODE   = "add-only"
      SEED_PATHS  = join("\n", ["README.md", "helm-chart-pipeline.yaml", "script"])
      SOURCE_REPO = "/${local.platform_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id   = oci_devops_repository.platform_pipelines.id
    seed_mode = "add-only"
  }

  depends_on = [
    local_file.helm_chart_pipeline,
    local_file.platform_pipelines_readme
  ]
}

resource "null_resource" "seed_platform_entities" {
  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.platform_pipelines.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS = join("\n", concat(
        [for name in sort(keys(local.applications_by_name)) : "${name}-package-pipeline.yaml"],
        [for name in sort(keys(local.generated_component_build_specs)) : local.generated_component_build_specs[name].build_spec_path],
        [for name in sort(keys(local.components_by_name)) : "${name}-release-pipeline.yaml"],
        sort(local.custom_build_spec_paths)
      ))
      SOURCE_REPO = "/${local.platform_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id                    = oci_devops_repository.platform_pipelines.id
    application_names          = join(",", sort(keys(local.applications_by_name)))
    component_names            = join(",", sort(keys(local.components_by_name)))
    generated_build_spec_paths = join(",", sort([for component in values(local.generated_component_build_specs) : component.build_spec_path]))
    custom_build_spec_paths    = join(",", sort(local.custom_build_spec_paths))
  }

  depends_on = [
    null_resource.seed_platform_shared,
    local_file.application_baseline_pipeline,
    local_file.application_delivery_pipeline,
    local_file.custom_application_delivery_pipeline,
    local_file.release_pipeline
  ]
}

resource "null_resource" "refresh_platform_development" {
  count = var.development_mode ? 1 : 0

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.platform_pipelines.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "refresh"
      SEED_PATHS = join("\n", concat(
        ["README.md", "helm-chart-pipeline.yaml", "script"],
        [for name in sort(keys(local.applications_by_name)) : "${name}-package-pipeline.yaml"],
        [for name in sort(keys(local.generated_component_build_specs)) : local.generated_component_build_specs[name].build_spec_path],
        [for name in sort(keys(local.components_by_name)) : "${name}-release-pipeline.yaml"]
      ))
      SOURCE_REPO = "/${local.platform_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id = oci_devops_repository.platform_pipelines.id
    content_hash = sha256(join("", concat(
      [
        local_file.platform_pipelines_readme.content,
        local_file.helm_chart_pipeline.content,
      ],
      [for name in sort(keys(local.applications_by_name)) : local_file.application_baseline_pipeline[name].content],
      [for name in sort(keys(local.generated_component_build_specs)) : local_file.application_delivery_pipeline[name].content],
      [for name in sort(keys(local.components_by_name)) : local_file.release_pipeline[name].content],
      [
        for script_path in sort(fileset("${path.root}/${local.platform_repo_path}/script", "**")) :
        filesha256("${path.root}/${local.platform_repo_path}/script/${script_path}")
      ]
    )))
  }

  depends_on = [null_resource.seed_platform_entities]
}

resource "null_resource" "seed_application_source" {
  for_each = local.components_by_name

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.application_source[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS     = join("\n", ["README.md", "Dockerfile", ".oci-devops"])
      SOURCE_REPO    = "/${each.value.repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id        = oci_devops_repository.application_source[each.key].id
    component_name = each.key
    seed_mode      = "add-only"
  }

  depends_on = [
    local_file.application_source_dockerfile,
    local_file.application_source_env,
    local_file.application_source_pull_request_pipeline,
    local_file.application_source_readme
  ]
}

resource "null_resource" "seed_application_chart_baseline" {
  for_each = local.applications_by_name

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.application_chart[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS = join("\n", [
        "README.md",
        "${each.value.chart_path}/Chart.yaml",
        "${each.value.chart_path}/values.yaml",
        "${each.value.chart_path}/.helmignore"
      ])
      SOURCE_REPO = "/${each.value.repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id          = oci_devops_repository.application_chart[each.key].id
    application_name = each.key
    seed_mode        = "add-only"
  }

  depends_on = [
    local_file.application_chart_readme,
    local_file.application_chart_chart_yaml,
    local_file.application_chart_values_yaml,
    local_file.application_chart_helmignore
  ]
}

resource "null_resource" "seed_application_chart_components" {
  for_each = local.applications_by_name

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.application_chart[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS = join("\n", [
        for component in each.value.components : "${each.value.chart_path}/charts/${component.name}"
      ])
      SOURCE_REPO = "/${each.value.repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id          = oci_devops_repository.application_chart[each.key].id
    application_name = each.key
    component_names  = join(",", sort([for component in each.value.components : component.name]))
  }

  depends_on = [
    null_resource.seed_application_chart_baseline,
    local_file.component_chart_chart_yaml,
    local_file.component_chart_values_yaml,
    local_file.component_chart_deployment_yaml,
    local_file.component_chart_service_yaml,
    local_file.component_chart_serviceaccount_yaml
  ]
}
