resource "oci_devops_repository" "devops_pipelines_repo_flux" {
  name            = "pipelines"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing the source code for Build Pipelines in this project (Pipeline as Code)"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_variables_pipelines_flux" {
  filename = "${path.root}/${local.base_repo_path}/pipelines/variables.sh"
  content = templatefile("${path.root}/templates/variables.tpl", {
    repo_compartment_id = var.compartment_id
    repo_prefix         = var.ocir_repo_path_prefix
    region              = var.region
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "null_resource" "push_pipelines_repo_content_flux" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.devops_pipelines_repo_flux.0.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SOURCE_REPO    = "/${local.base_repo_path}/pipelines"
    }
    working_dir = path.root
  }
  triggers = {
    variables_file_sha256 = local_file.export_variables_pipelines_flux[0].content_sha256
    repo_id               = oci_devops_repository.devops_pipelines_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux]

  count = var.gitops_agent == "fluxcd" ? 1 : 0
}


resource "oci_devops_repository" "cluster_config_repo_flux" {
  name            = "cluster-config"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing Kubernetes cluster configurations related to infrastructure and system tools, to be used by cluster admins"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_values" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/infra-apps/flux-system/flux-operator/helm/values/base/values.yml"
  content = templatefile("${path.root}/templates/flux-operator-values.yaml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_bootstrap" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/bootstrap/flux-bootstrap.yml"
  content = templatefile("${path.root}/templates/flux-bootstrap.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
    git_repo_url      = oci_devops_repository.cluster_config_repo_flux.0.http_url
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "local_file" "export_flux_operator" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/types/example/flux-system/flux-operator.yml"
  content = templatefile("${path.root}/templates/flux-operator.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "null_resource" "push_cluster_config_repo_content_flux" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_config_repo_flux.0.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SOURCE_REPO    = "/${local.base_repo_path}/cluster-config"
    }
    working_dir = path.root
  }
  triggers = {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
    repo_id           = oci_devops_repository.cluster_config_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux, local_file.export_flux_values, local_file.export_flux_bootstrap, local_file.export_flux_operator]
  count      = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "oci_devops_repository" "apps_config_repo_flux" {
  name            = "apps-config"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing Kubernetes application configurations, to be used by developers"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "fluxcd" ? 1 : 0
}

resource "null_resource" "push_apps_config_repo_content_flux" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.apps_config_repo_flux.0.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SOURCE_REPO    = "/${local.base_repo_path}/apps-config"
    }
    working_dir = path.root
  }
  triggers = {
    repo_id = oci_devops_repository.apps_config_repo_flux.0.id
  }
  depends_on = [local_file.export_variables_pipelines_flux]
  count      = var.gitops_agent == "fluxcd" ? 1 : 0
}
