locals {
  base_app_repo_path = "repos"
  app_folders = toset([for file_dir in fileset("${path.root}/${local.base_app_repo_path}", "**") : split("/", file_dir).0])
}

resource "oci_devops_repository" "devops_pipelines_repo" {
  name       = "pipelines"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing the source code for Build Pipelines in this project (Pipeline as Code)"
  repository_type = "HOSTED"
}

resource "local_file" "export_variables" {
  filename = "${path.root}/repos/pipelines/variables.sh"
  content = templatefile("${path.root}/templates/variables.tpl", {
    repo_compartment_id = var.compartment_id
    repo_prefix = var.ocir_repo_path_prefix
    region = var.region
  })
}

# I am archiving just to get the sha of the folder
data "archive_file" "pipelines_archive" {
  output_path = "pipelines.zip"
  source_dir = "${path.root}/repos/pipelines"
  type        = "zip"
}

resource "null_resource" "push_pipelines_repo_content" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.devops_pipelines_repo.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/repos/pipelines"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.pipelines_archive.output_sha
    repo_id = oci_devops_repository.devops_pipelines_repo.id
  }
  depends_on = [local_file.export_variables]
}


resource "oci_devops_repository" "system_config_repo" {
  name       = "system-cluster-config"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing Kubernetes cluster configurations, to be used by cluster admins"
  repository_type = "HOSTED"
}

data "archive_file" "cluster_config_archive" {
  output_path = "system-cluster-config.zip"
  source_dir = "${path.root}/repos/system-cluster-config"
  type        = "zip"
}

resource "null_resource" "push_cluster_config_repo_content" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.system_config_repo.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/repos/system-cluster-config"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.cluster_config_archive.output_sha
    repo_id = oci_devops_repository.system_config_repo.id
  }
  depends_on = [local_file.export_variables]
}

resource "oci_devops_repository" "apps_config_repo" {
  name       = "apps-cluster-config"
  project_id = oci_devops_project.devops_project.id
  description = "Repository containing Kubernetes application configurations, to be used by developers"
  repository_type = "HOSTED"
}

data "archive_file" "apps_config_archive" {
  output_path = "apps-cluster-config.zip"
  source_dir = "${path.root}/repos/apps-cluster-config"
  type        = "zip"
}

resource "null_resource" "push_apps_config_repo_content" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.apps_config_repo.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/repos/apps-cluster-config"
    }
    working_dir = path.root
  }
  triggers = {
    src_hash = data.archive_file.apps_config_archive.output_sha
    repo_id = oci_devops_repository.apps_config_repo.id
  }
  depends_on = [local_file.export_variables]
}




# TO CONSIDER FOR FUTURE EXTENSION
/*resource "oci_devops_repository" "app_repository" {
  for_each = local.app_folders
  name       = each.value
  project_id = oci_devops_project.devops_project.id
  description = "Application repository for ${each.value}"
  repository_type = "HOSTED"
}

resource "null_resource" "push_app_repo_content" {

  for_each = oci_devops_repository.app_repository

  provisioner "local-exec" {
    command = "chmod +x ./scripts/push_repo.sh && ./scripts/push_repo.sh"
    environment = {
      REPO_CLONE_URL = each.value.http_url
      GIT_USERNAME = var.git_username
      GIT_PASSWORD = var.git_password
      REGION = var.region
      SOURCE_REPO = "/${local.base_app_repo_path}/${each.value.name}"
    }
    working_dir = path.root
  }
  triggers = {
    repo_id = each.value.id
  }
}
*/
