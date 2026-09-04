module "devops" {
  source = "./modules/devops"

  compartment_id                         = coalesce(var.devops_compartment_id, var.compartment_ocid)
  region                                 = var.region
  tenancy_id                             = var.tenancy_ocid
  git_username                           = local.git_username
  git_password                           = var.auth_token
  create_notification_topic              = var.create_notification_topic
  notification_topic_id                  = var.notification_topic_id
  notification_topic_name                = var.notification_topic_name
  notification_topic_description         = var.notification_topic_description
  devops_project_name                    = var.devops_project_name
  devops_project_description             = var.devops_project_description
  devops_log_group_name                  = var.devops_log_group_name
  devops_log_group_description           = var.devops_log_group_description
  devops_log_name                        = var.devops_log_name
  devops_log_is_enabled                  = var.devops_log_is_enabled
  devops_log_retention_period_in_days    = var.devops_log_retention_period_in_days
  oke_cluster_id                         = var.oke_cluster_id
  oke_worker_subnet_id                   = var.oke_worker_subnet_id
  oke_worker_nsg_id                      = var.oke_worker_nsg_id
  prod_oke_cluster_id                    = var.prod_oke_cluster_id
  prod_oke_compartment_id                = var.prod_oke_compartment_id
  prod_oke_worker_subnet_id              = var.prod_oke_worker_subnet_id
  prod_oke_worker_nsg_id                 = var.prod_oke_worker_nsg_id
  namespace_init_secret_name             = var.namespace_init_secret_name
  applications                           = local.application_config
  enable_cluster_admin                   = var.enable_cluster_admin
  cluster_admin_artifact_repository_name = var.cluster_admin_artifact_repository_name
  cluster_administration                 = jsondecode(var.cluster_administration)
  development_mode                       = var.development_mode
}

module "iam" {
  source = "./modules/iam"
  count  = var.create_iam ? 1 : 0

  compartment_id              = coalesce(var.devops_compartment_id, var.compartment_ocid)
  iam_domain_id               = var.devops_iam_domain_id
  network_compartment_id      = coalesce(var.network_compartment_id, var.compartment_ocid)
  prod_network_compartment_id = var.prod_network_compartment_id
  oke_compartment_id          = coalesce(var.oke_compartment_id, var.compartment_ocid)
  prod_oke_compartment_id     = var.prod_oke_compartment_id
  secret_compartment_id       = coalesce(var.namespace_init_secret_compartment_id, var.compartment_ocid)
  devops_policy_name          = var.devops_policy_name
  dynamic_group_name          = var.devops_dynamic_group_name
  providers = {
    oci = oci.home
  }
}
