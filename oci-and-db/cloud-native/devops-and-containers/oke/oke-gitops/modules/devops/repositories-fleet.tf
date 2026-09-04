resource "oci_devops_repository" "fleet_config_repo" {
  count           = var.enable_multicluster ? 1 : 0
  name            = "fleet-config"
  project_id      = oci_devops_project.devops_project.id
  description     = "Optional fleet configuration: native Argo CD or decentralized Flux CD"
  repository_type = "HOSTED"
}

resource "local_file" "export_flux_fleet_cluster_root" {
  for_each = local.flux_fleet_members

  filename = "${path.root}/repos/fleet-config/fluxcd/clusters/${each.key}/kustomization.yml"
  content = templatefile("${path.root}/templates/flux-fleet-cluster-kustomization.yml", {
    manages_operator      = each.value.manages_operator
    activates_development = each.value.activates_development
  })
}

resource "local_file" "export_flux_fleet_common_profile" {
  for_each = local.flux_fleet_members

  filename = "${path.root}/repos/fleet-config/fluxcd/clusters/${each.key}/common.yml"
  content = templatefile("${path.root}/templates/flux-fleet-profile.yml", {
    profile_name = "common"
    depends_on   = each.value.manages_operator ? "flux-operator" : ""
  })
}

resource "local_file" "export_flux_fleet_bootstrap" {
  count = var.enable_multicluster && var.gitops_agent == "fluxcd" ? 1 : 0

  filename = "${path.root}/repos/fleet-config/fluxcd/bootstrap/member-template.yml"
  content = templatefile("${path.root}/templates/flux-fleet-bootstrap.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
    fleet_repo_url    = oci_devops_repository.fleet_config_repo[0].http_url
    apps_repo_url     = oci_devops_repository.apps_config_repo_flux[0].http_url
    cluster_name      = "CHANGE_ME"
  })
}

resource "local_file" "export_flux_fleet_operator_values" {
  count = var.enable_multicluster && var.gitops_agent == "fluxcd" ? 1 : 0

  filename = "${path.root}/repos/fleet-config/fluxcd/profiles/flux-operator/values/00-bootstrap.yml"
  content = templatefile("${path.root}/templates/flux-operator-values.yaml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
}

resource "local_file" "export_flux_fleet_operator_resourceset" {
  count = var.enable_multicluster && var.gitops_agent == "fluxcd" ? 1 : 0

  filename = "${path.root}/repos/fleet-config/fluxcd/profiles/flux-operator/resourceset.yml"
  content = templatefile("${path.root}/templates/flux-operator-application.yml", {
    region_key        = local.region_key
    tenancy_namespace = local.namespace
    repo_prefix       = var.ocir_repo_path_prefix
  })
}

resource "local_file" "export_argocd_fleet_reference_app_infrastructure" {
  filename = "${path.root}/repos/fleet-config/argocd/examples/oke-example/applications/reference-app/infrastructure/application.yml"
  content = templatefile("${path.root}/templates/argocd-fleet-reference-app-infrastructure.yml", {
    fleet_config_repo_url = oci_devops_repository.fleet_config_repo[0].http_url
    cluster               = "oke-example"
  })
  count = var.enable_multicluster && var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_fleet_reference_app_components" {
  filename = "${path.root}/repos/fleet-config/argocd/examples/oke-example/applications/reference-app/components.application-set.yml"
  content = templatefile("${path.root}/templates/argocd-fleet-reference-app-components.yml", {
    apps_config_repo_url = oci_devops_repository.apps_config_repo_argocd[0].http_url
    cluster              = "oke-example"
  })
  count = var.enable_multicluster && var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_fleet_reference_helm_app_infrastructure" {
  filename = "${path.root}/repos/fleet-config/argocd/examples/oke-example/applications/reference-helm-app/infrastructure/application.yml"
  content = templatefile("${path.root}/templates/argocd-fleet-reference-helm-app-infrastructure.yml", {
    fleet_config_repo_url = oci_devops_repository.fleet_config_repo[0].http_url
    cluster               = "oke-example"
  })
  count = var.enable_multicluster && var.gitops_agent == "argocd" ? 1 : 0
}

resource "local_file" "export_argocd_fleet_reference_helm_app_components" {
  filename = "${path.root}/repos/fleet-config/argocd/examples/oke-example/applications/reference-helm-app/components.application-set.yml"
  content = templatefile("${path.root}/templates/argocd-fleet-reference-helm-app-components.yml", {
    apps_config_repo_url = oci_devops_repository.apps_config_repo_argocd[0].http_url
    cluster              = "oke-example"
  })
  count = var.enable_multicluster && var.gitops_agent == "argocd" ? 1 : 0
}

resource "null_resource" "push_fleet_config_repo_content" {
  count = var.enable_multicluster ? 1 : 0

  provisioner "local-exec" {
    command = "chmod +x ./script/push_repo.sh && ./script/push_repo.sh"
    environment = {
      REPO_CLONE_URL       = oci_devops_repository.fleet_config_repo[0].http_url
      GIT_USERNAME         = var.git_username
      GIT_PASSWORD         = var.git_password
      REGION               = var.region
      SOURCE_REPO          = "/repos/fleet-config/${var.gitops_agent}"
      OVERWRITE_REPOSITORY = tostring(var.development_overwrite_repositories)
    }
    working_dir = path.root
  }

  triggers = {
    repo_id               = oci_devops_repository.fleet_config_repo[0].id
    seed_revision         = local.repository_seed_revision
    development_overwrite = var.development_overwrite_repositories ? timestamp() : "false"
  }

  depends_on = [
    local_file.export_argocd_fleet_reference_app_infrastructure,
    local_file.export_argocd_fleet_reference_app_components,
    local_file.export_argocd_fleet_reference_helm_app_infrastructure,
    local_file.export_argocd_fleet_reference_helm_app_components,
    local_file.export_flux_fleet_cluster_root,
    local_file.export_flux_fleet_common_profile,
    local_file.export_flux_fleet_bootstrap,
    local_file.export_flux_fleet_operator_values,
    local_file.export_flux_fleet_operator_resourceset
  ]
}
