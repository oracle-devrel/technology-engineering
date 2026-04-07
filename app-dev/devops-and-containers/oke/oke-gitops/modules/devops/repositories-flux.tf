locals {
  flux_controller_versions_by_chart = {
    "0.45.1" = {
      helm_controller_version      = "v1.5.3"
      kustomize_controller_verison = "v1.8.2"
      source_controller_version    = "v1.8.1"
    }
  }

  default_flux_controller_versions = {
    helm_controller_version      = "v1.5.3"
    kustomize_controller_verison = "v1.8.2"
    source_controller_version    = "v1.8.1"
  }

  selected_flux_controller_versions = lookup(
    local.flux_controller_versions_by_chart,
    var.flux_agent_chart_version,
    local.default_flux_controller_versions
  )

  helm_controller_version      = local.selected_flux_controller_versions.helm_controller_version
  kustomize_controller_verison = local.selected_flux_controller_versions.kustomize_controller_verison
  source_controller_version    = local.selected_flux_controller_versions.source_controller_version
}


resource "oci_devops_repository" "devops_pipelines_repo_flux" {
  name       = "pipelines"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing the source code for Build Pipelines in this project (Pipeline as Code)"
  repository_type = "HOSTED"
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_variables_pipelines_flux" {
  filename = "${path.root}/${local.base_repo_path}/pipelines/variables.sh"
  content = templatefile("${path.root}/templates/variables.tpl", {
    repo_compartment_id = var.compartment_id
    repo_prefix = var.ocir_repo_path_prefix
    region = var.region
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_mirror_flux_variables" {
  filename = "${path.root}/${local.base_repo_path}/pipelines/flux-vars.sh"
  content = templatefile("${path.root}/templates/flux-vars.tpl", {
    flux_chart_version = var.flux_agent_chart_version
    helm_controller_version = local.helm_controller_version
    kustomize_controller_version = local.kustomize_controller_verison
    source_controller_version = local.source_controller_version
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

# I am archiving just to get the sha of the folder
data "archive_file" "pipelines_archive_flux" {
  output_path = "pipelines.zip"
  source_dir = "${path.root}/${local.base_repo_path}/pipelines"
  type        = "zip"
}

resource "null_resource" "push_pipelines_repo_content_flux" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.devops_pipelines_repo_flux.0.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/${local.base_repo_path}/pipelines"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.pipelines_archive_flux.output_sha
    repo_id = oci_devops_repository.devops_pipelines_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux, local_file.export_mirror_flux_variables]

  count = var.gitops_agent == "fluxcd" ? 1 : 0
}


resource "oci_devops_repository" "cluster_config_repo_flux" {
  name       = "cluster-config"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing Kubernetes cluster configurations related to infrastructure and system tools, to be used by cluster admins"
  repository_type = "HOSTED"
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_values" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/infra-apps/flux-system/flux-operator/helm/values/base/values.yml"
  content = templatefile("${path.root}/templates/flux-operator-values.yaml", {
    region_key = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix = var.ocir_repo_path_prefix
    chart_version = var.flux_agent_chart_version
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_bootstrap" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/bootstrap/flux-bootstrap.yml"
  content = templatefile("${path.root}/templates/flux-bootstrap.yml", {
    region_key = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix = var.ocir_repo_path_prefix
    git_repo_url = oci_devops_repository.cluster_config_repo_flux.0.http_url
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_operator" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/types/example/flux-system/flux-operator.yml"
  content = templatefile("${path.root}/templates/flux-operator.yml", {
    region_key = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

data "archive_file" "cluster_config_archive_flux" {
  output_path = "cluster-config.zip"
  source_dir = "${path.root}/${local.base_repo_path}/cluster-config"
  type        = "zip"
}

resource "null_resource" "push_cluster_config_repo_content" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_config_repo_flux.0.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/${local.base_repo_path}/cluster-config"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.cluster_config_archive_flux.output_sha
    repo_id = oci_devops_repository.cluster_config_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux, local_file.export_flux_values, local_file.export_flux_bootstrap, local_file.export_flux_operator]
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "oci_devops_repository" "apps_config_repo_flux" {
  name       = "apps-config"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing Kubernetes application configurations, to be used by developers"
  repository_type = "HOSTED"
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

data "archive_file" "apps_config_archive_flux" {
  output_path = "apps-config.zip"
  source_dir = "${path.root}/${local.base_repo_path}/apps-config"
  type        = "zip"
}

resource "null_resource" "push_apps_config_repo_content" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.apps_config_repo_flux.0.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/${local.base_repo_path}/apps-config"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.apps_config_archive_flux.output_sha
    repo_id = oci_devops_repository.apps_config_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux]
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}
