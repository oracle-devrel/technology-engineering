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
      REPO_CLONE_URL       = oci_devops_repository.devops_pipelines_repo_argocd.0.http_url
      GIT_USERNAME         = var.git_username
      GIT_PASSWORD         = var.git_password
      REGION               = var.region
      SOURCE_REPO          = "/${local.base_repo_path}/pipelines"
      OVERWRITE_REPOSITORY = tostring(var.development_overwrite_repositories)
    }
    working_dir = path.root
  }
  triggers = {
    variables_file_sha256 = local_file.export_variables_pipelines_argocd[0].content_sha256
    repo_id               = oci_devops_repository.devops_pipelines_repo_argocd.0.id
    seed_revision         = local.repository_seed_revision
    development_overwrite = var.development_overwrite_repositories ? timestamp() : "false"
  }
  lifecycle {
    # OCI Resource Manager uses an ephemeral filesystem, so local_file appears
    # absent on later jobs. Ignore this legacy trigger to avoid replacing and
    # overwriting the customer-owned pipelines repository on every apply.
    ignore_changes = [triggers["variables_file_sha256"]]
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
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/argocd/values/00-bootstrap.yml"
  content = templatefile("${path.root}/templates/argocd-values.yaml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_bootstrap" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/bootstrap/argocd-bootstrap.yml"
  content = templatefile("${path.root}/templates/argocd-bootstrap.yml", {
    git_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_operator" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/argocd/helm-repository.application.yaml"
  content = templatefile("${path.root}/templates/argocd.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_platform" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/argocd/platform.yml"
  content = templatefile("${path.root}/templates/argocd-platform.yml", {
    git_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_apps" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/argocd/apps.yml"
  content = templatefile("${path.root}/templates/argocd-apps.yml", {
    cluster_config_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_projects" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/argocd/projects.yml"
  content = templatefile("${path.root}/templates/argocd-projects.yml", {
    cluster_config_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
    apps_config_repo_url    = oci_devops_repository.apps_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_reference_app_infrastructure" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/reference-app/infrastructure/application.yml"
  content = templatefile("${path.root}/templates/argocd-reference-app-infrastructure.yml", {
    cluster_config_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_reference_app_components" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/reference-app/components.application-set.yml"
  content = templatefile("${path.root}/templates/argocd-reference-app-components.yml", {
    apps_config_repo_url = oci_devops_repository.apps_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_reference_helm_app_infrastructure" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/reference-helm-app/infrastructure/application.yml"
  content = templatefile("${path.root}/templates/argocd-reference-helm-app-infrastructure.yml", {
    cluster_config_repo_url = oci_devops_repository.cluster_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_reference_helm_app_components" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/platform/applications/reference-helm-app/components.application-set.yml"
  content = templatefile("${path.root}/templates/argocd-reference-helm-app-components.yml", {
    apps_config_repo_url = oci_devops_repository.apps_config_repo_argocd.0.http_url
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_fleet" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/gitops/argocd/fleet.yml"
  content = templatefile("${path.root}/templates/argocd-fleet.yml", {
    fleet_config_repo_url = oci_devops_repository.fleet_config_repo[0].http_url
  })
  count = var.gitops_agent == "argocd" && var.enable_multicluster ? 1 : 0
}

resource "null_resource" "upsert_argocd_fleet_adapter" {
  count = var.gitops_agent == "argocd" && var.enable_multicluster ? 1 : 0

  provisioner "local-exec" {
    command = "chmod +x ./script/upsert_repo_file.sh && ./script/upsert_repo_file.sh"
    environment = {
      REPO_CLONE_URL       = oci_devops_repository.cluster_config_repo_argocd[0].http_url
      GIT_USERNAME         = var.git_username
      GIT_PASSWORD         = var.git_password
      SOURCE_FILE          = "/${local.base_repo_path}/cluster-config/gitops/argocd/fleet.yml"
      TARGET_FILE          = "gitops/argocd/fleet.yml"
      OVERWRITE_REPOSITORY = tostring(var.development_overwrite_repositories)
    }
    working_dir = path.root
  }

  triggers = {
    adapter_sha256 = sha256(templatefile("${path.root}/templates/argocd-fleet.yml", {
      fleet_config_repo_url = oci_devops_repository.fleet_config_repo[0].http_url
    }))
    repo_id               = oci_devops_repository.cluster_config_repo_argocd[0].id
    development_overwrite = var.development_overwrite_repositories ? timestamp() : "false"
  }

  depends_on = [
    null_resource.push_cluster_config_repo_content_argocd,
    null_resource.push_fleet_config_repo_content
  ]
}

resource "local_file" "export_argocd_git_credentials" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/bootstrap/oci-devops-git-credentials.yml"
  content = templatefile("${path.root}/templates/argocd-git-repo-creds.yml", {
    git_repo_url_prefix = trimsuffix(oci_devops_repository.cluster_config_repo_argocd.0.http_url, "/cluster-config")
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_ocir_credentials" {
  filename = "${path.root}/${local.base_repo_path}/cluster-config/bootstrap/ocir-credentials.yml"
  content = templatefile("${path.root}/templates/argocd-ocir-credentials.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
  count = var.gitops_agent == "argocd" ? 1 : 0
}

resource "null_resource" "push_cluster_config_repo_content_argocd" {

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL       = oci_devops_repository.cluster_config_repo_argocd.0.http_url
      GIT_USERNAME         = var.git_username
      GIT_PASSWORD         = var.git_password
      REGION               = var.region
      SOURCE_REPO          = "/${local.base_repo_path}/cluster-config"
      OVERWRITE_REPOSITORY = tostring(var.development_overwrite_repositories)
    }
    working_dir = path.root
  }
  triggers = {
    region_key            = local.region_key
    tenancy_namespace     = local.namespace
    repo_prefix           = var.ocir_repo_path_prefix
    repo_id               = oci_devops_repository.cluster_config_repo_argocd.0.id
    seed_revision         = local.repository_seed_revision
    development_overwrite = var.development_overwrite_repositories ? timestamp() : "false"
  }
  depends_on = [
    local_file.export_variables_pipelines_argocd,
    local_file.export_argocd_values,
    local_file.export_argocd_bootstrap,
    local_file.export_argocd_operator,
    local_file.export_argocd_platform,
    local_file.export_argocd_apps,
    local_file.export_argocd_projects,
    local_file.export_argocd_reference_app_infrastructure,
    local_file.export_argocd_reference_app_components,
    local_file.export_argocd_reference_helm_app_infrastructure,
    local_file.export_argocd_reference_helm_app_components,
    local_file.export_argocd_fleet,
    local_file.export_argocd_git_credentials,
    local_file.export_argocd_ocir_credentials
  ]
  count = var.gitops_agent == "argocd" ? 1 : 0
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
      REPO_CLONE_URL       = oci_devops_repository.apps_config_repo_argocd.0.http_url
      GIT_USERNAME         = var.git_username
      GIT_PASSWORD         = var.git_password
      REGION               = var.region
      SOURCE_REPO          = "/${local.base_repo_path}/apps-config"
      OVERWRITE_REPOSITORY = tostring(var.development_overwrite_repositories)
    }
    working_dir = path.root
  }
  triggers = {
    repo_id               = oci_devops_repository.apps_config_repo_argocd.0.id
    seed_revision         = local.repository_seed_revision
    development_overwrite = var.development_overwrite_repositories ? timestamp() : "false"
  }
  depends_on = [local_file.export_variables_pipelines_argocd]
  count      = var.gitops_agent == "argocd" ? 1 : 0
}
