resource "oci_devops_repository" "devops_pipelines_repo_argocd" {
  name            = "pipelines"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing the source code for Build Pipelines in this project (Pipeline as Code)"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_variables_pipelines_argocd" {
  filename = "${path.root}/${local.base_repo_path}/pipelines/variables.sh"
  content = templatefile("${path.root}/templates/variables.tpl", {
    repo_compartment_id = var.compartment_id
    repo_prefix         = var.ocir_repo_path_prefix
    region              = var.region
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "null_resource" "push_pipelines_repo_content_argocd" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SOURCE_REPO    = "/${local.base_repo_path}/pipelines"
    }
    working_dir = path.root
  }
  triggers = {
    variables_file_sha256 = local_file.export_variables_pipelines_argocd[0].content_sha256
    repo_id               = oci_devops_repository.devops_pipelines_repo_argocd.0.id
  }
  depends_on = [local_file.export_variables_pipelines_argocd]

  count = var.gitops_agent == "argocd" ? 1 : 0
}


resource "oci_devops_repository" "cluster_config_repo_argocd" {
  name            = "cluster-config"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing Kubernetes cluster configurations related to infrastructure and system tools, to be used by cluster admins"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_values" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/infra-apps/argocd/argocd/helm/values/base/values.yml"
  content = templatefile("${path.root}/templates/argocd-values.yaml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_bootstrap" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/bootstrap/argocd-bootstrap.yml"
  content = templatefile("${path.root}/templates/argocd-bootstrap.yml", {
    git_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_operator" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/types/example/argocd/argocd.yml"
  content = templatefile("${path.root}/templates/argocd.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
    git_repo_url      = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "null_resource" "push_cluster_config_repo_content_argocd" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_config_repo_argocd.0.http_url
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
    repo_id           = oci_devops_repository.cluster_config_repo_argocd.0.id
  }
  depends_on = [local_file.export_variables_pipelines_argocd, local_file.export_argocd_values, local_file.export_argocd_bootstrap, local_file.export_argocd_operator]
  count      = var.gitops_agent == "argocd" ? 1 : 0
}

resource "oci_devops_repository" "apps_config_repo_argocd" {
  name            = "apps-config"
  project_id      = oci_devops_project.devops_project.id
  description     = "Repository containing Kubernetes application configurations, to be used by developers"
  repository_type = "HOSTED"
  count           = var.gitops_agent == "argocd" ? 1 : 0
}

resource "null_resource" "push_apps_config_repo_content_argocd" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.apps_config_repo_argocd.0.http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SOURCE_REPO    = "/${local.base_repo_path}/apps-config"
    }
    working_dir = path.root
  }
  triggers = {
    repo_id = oci_devops_repository.apps_config_repo_argocd.0.id
  }
  depends_on = [local_file.export_variables_pipelines_argocd]
  count      = var.gitops_agent == "argocd" ? 1 : 0
}
