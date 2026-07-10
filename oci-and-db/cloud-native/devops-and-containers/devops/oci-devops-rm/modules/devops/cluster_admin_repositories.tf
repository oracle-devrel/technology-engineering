resource "oci_devops_repository" "cluster_admin" {
  for_each = local.cluster_admin_singleton

  name            = "cluster-admin"
  project_id      = oci_devops_project.devops_project.id
  description     = "Cluster administrator-owned Kubernetes resources, tool catalog, and per-cluster Helm values"
  repository_type = "HOSTED"
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "configuration-repository"
  })

  lifecycle {
    ignore_changes = all
  }
}

resource "oci_artifacts_repository" "cluster_admin_values" {
  for_each = local.cluster_admin_singleton

  compartment_id = var.compartment_id
  display_name = trimspace(var.cluster_admin_artifact_repository_name) != "" ? (
    var.cluster_admin_artifact_repository_name
  ) : "${local.project_repo_prefix}-cluster-admin-values"
  description     = "Immutable per-commit Helm values and cluster plans published by cluster administration"
  is_immutable    = true
  repository_type = "GENERIC"
  freeform_tags = merge(local.cluster_admin_tags, {
    role = "values-repository"
  })

  lifecycle {
    ignore_changes = all
  }
}

resource "local_file" "cluster_admin_readme" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/README.md"
  content = templatefile("${path.root}/templates/cluster-admin-README.md.tpl", {
    project_name = var.devops_project_name
  })
}

resource "local_file" "cluster_admin_catalog" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/catalog/tools.yaml"
  content = templatefile("${path.root}/templates/cluster-admin-tools.yaml.tpl", {
    tools = local.cluster_admin_tools
  })
}

resource "local_file" "cluster_admin_build_spec" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/.oci-devops/build-pipeline.yaml"
  content = templatefile("${path.root}/templates/cluster-admin-build-pipeline.yaml.tpl", {
    artifact_repository_id = oci_artifacts_repository.cluster_admin_values[each.key].id
    compartment_id         = var.compartment_id
    mirror_pipeline_id     = oci_devops_build_pipeline.cluster_admin_mirror[each.key].id
    project_id             = oci_devops_project.devops_project.id
    region                 = var.region
    region_key             = local.region_key
    tenancy_namespace      = local.namespace
    chart_repo_prefix      = "${local.project_repo_prefix}/charts/cluster-tools"
  })
}

resource "local_file" "cluster_admin_mirror_spec" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/.oci-devops/mirror-charts-pipeline.yaml"
  content = templatefile("${path.root}/templates/cluster-admin-mirror-pipeline.yaml.tpl", {
    compartment_id    = var.compartment_id
    region            = var.region
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    chart_repo_prefix = "${local.project_repo_prefix}/charts/cluster-tools"
  })
}

resource "local_file" "cluster_admin_pr_spec" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/.oci-devops/pull-request-pipeline.yaml"
  content  = templatefile("${path.root}/templates/cluster-admin-pr-pipeline.yaml.tpl", {})
}

resource "local_file" "cluster_admin_baseline_example" {
  for_each = local.cluster_admin_clusters

  filename = "${path.root}/${local.cluster_admin_repo_path}/clusters/${each.key}/baseline/README.md"
  content  = "# ${title(each.key)} cluster baseline\n\nPlace cluster-scoped Kubernetes YAML here. Removing a file does not delete the live object.\n"
}

resource "local_file" "cluster_admin_tool_values" {
  for_each = local.cluster_admin_tool_pairs

  filename = "${path.root}/${local.cluster_admin_repo_path}/clusters/${each.value.cluster_name}/tools/${each.value.tool_name}/values.yaml"
  content  = "# ${each.value.cluster_name} values for ${each.value.tool_name}\n{}\n"
}

resource "local_file" "cluster_admin_tool_metadata" {
  for_each = local.cluster_admin_tool_pairs

  filename = "${path.root}/${local.cluster_admin_repo_path}/clusters/${each.value.cluster_name}/tools/${each.value.tool_name}/tool.yaml"
  content = yamlencode({
    depends_on = each.value.dependencies
    name       = each.value.tool_name
    namespace  = each.value.namespace
  })
}

resource "local_file" "cluster_admin_tool_resources_readme" {
  for_each = local.cluster_admin_tool_pairs

  filename = "${path.root}/${local.cluster_admin_repo_path}/clusters/${each.value.cluster_name}/tools/${each.value.tool_name}/resources/README.md"
  content  = "# Supplemental resources\n\nPlace namespaced Kubernetes YAML for `${each.value.namespace}` here. Plain Kubernetes Secret objects are rejected; use ExternalSecret resources.\n"
}

resource "local_file" "cluster_admin_validate_script" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/script/validate-config.py"
  content  = file("${path.root}/repos/cluster-admin/script/validate-config.py")
}

resource "local_file" "cluster_admin_mirror_script" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/script/mirror-charts.py"
  content  = file("${path.root}/repos/cluster-admin/script/mirror-charts.py")
}

resource "local_file" "cluster_admin_publish_script" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/script/publish-and-dispatch.py"
  content  = file("${path.root}/repos/cluster-admin/script/publish-and-dispatch.py")
}

resource "local_file" "cluster_admin_deploy_script" {
  for_each = local.cluster_admin_singleton

  filename = "${path.root}/${local.cluster_admin_repo_path}/script/deploy-cluster.py"
  content  = file("${path.root}/repos/cluster-admin/script/deploy-cluster.py")
}

resource "null_resource" "seed_cluster_admin" {
  for_each = local.cluster_admin_singleton

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_admin[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS     = join("\n", ["README.md", "catalog", ".oci-devops", "script"])
      SOURCE_REPO    = "/${local.cluster_admin_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id       = oci_devops_repository.cluster_admin[each.key].id
    seed_contract = "cluster-admin-shared-v1"
  }

  depends_on = [
    local_file.cluster_admin_readme,
    local_file.cluster_admin_catalog,
    local_file.cluster_admin_build_spec,
    local_file.cluster_admin_mirror_spec,
    local_file.cluster_admin_pr_spec,
    local_file.cluster_admin_validate_script,
    local_file.cluster_admin_mirror_script,
    local_file.cluster_admin_publish_script,
    local_file.cluster_admin_deploy_script
  ]
}

resource "null_resource" "sync_cluster_admin_catalog" {
  for_each = local.cluster_admin_singleton

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_admin[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "refresh"
      SEED_PATHS     = "catalog/tools.yaml"
      SOURCE_REPO    = "/${local.cluster_admin_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id      = oci_devops_repository.cluster_admin[each.key].id
    catalog_hash = sha256(local_file.cluster_admin_catalog[each.key].content)
  }

  depends_on = [null_resource.seed_cluster_admin]
}

resource "null_resource" "seed_cluster_admin_entities" {
  for_each = local.cluster_admin_singleton

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_admin[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      SEED_MODE      = "add-only"
      SEED_PATHS = join("\n", concat(
        [for cluster_name in sort(keys(local.cluster_admin_clusters)) : "clusters/${cluster_name}/baseline"],
        [
          for key in sort(keys(local.cluster_admin_tool_pairs)) :
          "clusters/${local.cluster_admin_tool_pairs[key].cluster_name}/tools/${local.cluster_admin_tool_pairs[key].tool_name}"
        ]
      ))
      SOURCE_REPO = "/${local.cluster_admin_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id = oci_devops_repository.cluster_admin[each.key].id
    targets = join(",", sort(keys(local.cluster_admin_tool_pairs)))
  }

  depends_on = [
    null_resource.sync_cluster_admin_catalog,
    local_file.cluster_admin_baseline_example,
    local_file.cluster_admin_tool_metadata,
    local_file.cluster_admin_tool_values,
    local_file.cluster_admin_tool_resources_readme
  ]
}

resource "null_resource" "refresh_cluster_admin_development" {
  for_each = var.development_mode ? local.cluster_admin_singleton : {}

  provisioner "local-exec" {
    command = "chmod +x ./script/seed_repo.sh && ./script/seed_repo.sh"
    environment = {
      REPO_CLONE_URL = oci_devops_repository.cluster_admin[each.key].http_url
      GIT_USERNAME   = var.git_username
      GIT_PASSWORD   = var.git_password
      REGION         = var.region
      REMOVE_PATHS   = "script/deploy-production.py"
      SEED_MODE      = "refresh"
      SEED_PATHS     = join("\n", ["README.md", ".oci-devops", "script"])
      SOURCE_REPO    = "/${local.cluster_admin_repo_path}"
    }
    working_dir = path.root
  }

  triggers = {
    repo_id = oci_devops_repository.cluster_admin[each.key].id
    content_hash = sha256(join("", [
      local_file.cluster_admin_readme[each.key].content,
      local_file.cluster_admin_build_spec[each.key].content,
      local_file.cluster_admin_mirror_spec[each.key].content,
      local_file.cluster_admin_pr_spec[each.key].content,
      local_file.cluster_admin_validate_script[each.key].content,
      local_file.cluster_admin_mirror_script[each.key].content,
      local_file.cluster_admin_publish_script[each.key].content,
      local_file.cluster_admin_deploy_script[each.key].content,
    ]))
  }

  depends_on = [null_resource.sync_cluster_admin_catalog]
}
