module "devops" {
  source                              = "./modules/devops"
  compartment_id                      = var.devops_compartment_id # Both DevOps project and OCIR will be here
  create_devops_project               = var.create_devops_project
  existing_devops_project_id          = var.existing_devops_project_id
  region                              = var.region
  tenancy_id                          = var.tenancy_ocid
  create_notification_topic           = var.create_notification_topic
  notification_topic_id               = var.notification_topic_id
  notification_topic_name             = var.notification_topic_name
  notification_topic_description      = var.notification_topic_description
  devops_project_name                 = var.devops_project_name
  devops_project_description          = var.devops_project_description
  devops_log_group_name               = var.devops_log_group_name
  devops_log_group_description        = var.devops_log_group_description
  devops_log_retention_period_in_days = var.devops_log_retention_period_in_days
  gitops_agent                        = var.gitops_agent
  gitops_scope                        = var.gitops_scope
  enable_multicluster                 = var.enable_multicluster
  flux_fleet_member_name              = var.flux_fleet_member_name
  development_overwrite_repositories  = var.development_overwrite_repositories

  git_username              = local.git_username
  git_password              = var.auth_token
  ocir_repo_path_prefix     = var.ocir_repo_path_prefix
  pipelines_repository_name = var.pipelines_repository_name

  # OKE ENVIRONMENT
  oke_cluster_id              = var.oke_cluster_id
  oke_environment_name        = var.oke_environment_name
  oke_environment_description = var.oke_environment_description
  oke_worker_subnet_id        = var.oke_worker_subnet_id
  oke_worker_nsg_id           = var.oke_worker_nsg_id
}

module "iam" {
  source                 = "./modules/iam"
  compartment_id         = module.devops.devops_project_compartment_id
  iam_domain_id          = var.devops_iam_domain_id
  kms_compartment_id     = var.kms_compartment_id
  network_compartment_id = var.network_compartment_id
  oke_compartment_id     = var.oke_compartment_id
  devops_policy_name     = var.devops_policy_name
  dynamic_group_name     = var.devops_dynamic_group_name
  count                  = var.create_iam ? 1 : 0
  providers              = { oci = oci.home }
}
