module "devops" {
  source = "./modules/devops"
  compartment_id = var.devops_compartment_id # Both DevOps project and OCIR will be here
  region = var.region
  tenancy_id = var.tenancy_ocid
  create_notification_topic = var.create_notification_topic
  notification_topic_id = var.notification_topic_id
  notification_topic_name = var.notification_topic_name
  notification_topic_description = var.notification_topic_description
  devops_project_name = var.devops_project_name
  devops_project_description = var.devops_project_description
  devops_log_group_name = var.devops_log_group_name
  devops_log_group_description = var.devops_log_group_description
  devops_log_retention_period_in_days = var.devops_log_retention_period_in_days

  git_username = local.git_username
  git_password = var.auth_token
  ocir_repo_path_prefix = var.ocir_repo_path_prefix

  # OKE ENVIRONMENT
  oke_cluster_id = var.oke_cluster_id
  oke_environment_name = var.oke_environment_name
  oke_environment_description = var.oke_environment_description
  is_oke_cluster_private = var.is_oke_cluster_private
  oke_worker_subnet_id = var.oke_worker_subnet_id
  oke_worker_nsg_id = var.oke_worker_nsg_id
}

module "iam" {
  source = "./modules/iam"
  tenancy_id = var.tenancy_ocid
  compartment_id = var.devops_compartment_id
  network_compartment_id = var.network_compartment_id
  oke_compartment_id = var.oke_compartment_id
  devops_policy_name = var.devops_policy_name
  domain_name = var.identity_domain_name
  dynamic_group_name = var.devops_dynamic_group_name
  is_oke_cluster_private = var.is_oke_cluster_private
  count = var.create_iam ? 1 : 0
  providers = {oci = oci.home}
}