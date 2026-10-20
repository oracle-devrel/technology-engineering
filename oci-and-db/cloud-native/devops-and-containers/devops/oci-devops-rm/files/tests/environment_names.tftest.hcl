mock_provider "oci" {
  mock_data "oci_identity_region_subscriptions" {
    defaults = {
      region_subscriptions = [{ region_name = "eu-milan-1", region_key = "MIL", is_home_region = true }]
    }
  }
  mock_data "oci_artifacts_container_configuration" {
    defaults = { namespace = "testnamespace" }
  }
}
mock_provider "local" {}
mock_provider "null" {}

variables {
  compartment_id                      = "ocid1.compartment.oc1..test"
  create_devops_project               = true
  existing_devops_project_id          = null
  application_delivery_mode           = "oci_devops"
  devops_pipeline_repository_name     = "devops-pipelines"
  region                              = "eu-milan-1"
  tenancy_id                          = "ocid1.tenancy.oc1..test"
  git_username                        = "test/user"
  git_password                        = "mock-token"
  create_notification_topic           = true
  notification_topic_id               = null
  notification_topic_name             = "test-topic"
  notification_topic_description      = "Test"
  devops_project_name                 = "test-project"
  devops_project_description          = "Test"
  devops_log_group_name               = "test-logs"
  devops_log_group_description        = "Test"
  devops_log_name                     = "test-log"
  devops_log_is_enabled               = true
  devops_log_retention_period_in_days = 30
  oke_cluster_id                      = "ocid1.cluster.oc1.eu-milan-1.test"
  prod_oke_cluster_id                 = "ocid1.cluster.oc1.eu-milan-1.test"
  oke_worker_subnet_id                = "ocid1.subnet.oc1.eu-milan-1.test"
  prod_oke_worker_subnet_id           = "ocid1.subnet.oc1.eu-milan-1.test"
  oke_worker_nsg_id                   = null
  namespace_init_secret_name          = "ocirsecret"
  applications = [
    { name = "shop", components = [{ name = "invoice" }, { name = "checkout" }] },
    { name = "orders", components = [{ name = "fulfillment" }] }
  ]
  enable_cluster_admin = true
  cluster_administration = {
    tools = [{ name = "metrics", repository = "https://charts.example.test", chart = "metrics", version = "1.0.0" }]
  }
}

run "defaults_preserve_contract" {
  command = plan
  module { source = "./modules/devops" }
  assert {
    condition = (
      oci_devops_deploy_stage.deploy_component["invoice:dev"].release_name == "invoice-dev" &&
      oci_devops_deploy_stage.deploy_component["invoice:staging"].release_name == "invoice-staging" &&
      oci_devops_deploy_stage.deploy_component_prod["invoice"].release_name == "invoice" &&
      oci_devops_deploy_pipeline.cluster_admin["noprod"].display_name == "cluster-admin-noprod" &&
      oci_devops_deploy_pipeline.cluster_admin["prod"].display_name == "cluster-admin-prod"
    )
    error_message = "Default release and pipeline names must remain unchanged."
  }
}

run "custom_names_keep_roles_and_keys" {
  command = plan
  module { source = "./modules/devops" }
  override_resource {
    target          = oci_devops_repository.cluster_admin["enabled"]
    override_during = plan
    values          = { id = "ocid1.devopsrepository.oc1.eu-milan-1.test" }
  }
  variables {
    environment_names = { dev = "development", staging = "uat", prod = "live", noprod_cluster = "sandbox", prod_cluster = "production" }
  }
  assert {
    condition = (
      length(local.component_environment_pairs) == 6 &&
      oci_devops_deploy_stage.deploy_component["invoice:dev"].release_name == "invoice-development" &&
      oci_devops_build_pipeline_stage.trigger_dev_deployment["invoice"].display_name == "Invoice Development Deploy" &&
      oci_devops_build_pipeline_stage.trigger_application_baseline_deployment["shop"].display_name == "Shop Sandbox Deploy" &&
      oci_devops_deploy_stage.deploy_component["fulfillment:staging"].release_name == "fulfillment-uat" &&
      oci_devops_deploy_pipeline.deploy_component["checkout:staging"].display_name == "checkout-release" &&
      oci_devops_deploy_stage.deploy_component_prod["invoice"].release_name == "invoice"
    )
    error_message = "Names must change while entity keys and production release identity stay stable."
  }
  assert {
    condition = (
      oci_devops_deploy_pipeline.cluster_admin["noprod"].freeform_tags.cluster == "sandbox" &&
      oci_devops_deploy_pipeline.cluster_admin["prod"].display_name == "cluster-admin-production" &&
      keys(oci_devops_deploy_stage.cluster_admin_approval) == ["prod"] &&
      keys(oci_devops_deploy_stage.cluster_admin_decommission_approval) == ["prod"] &&
      length(oci_devops_deploy_stage.approve_component_prod_release) == 3
    )
    error_message = "Production approvals must remain tied to workflow roles."
  }
  assert {
    condition = (
      endswith(local_file.cluster_admin_baseline_example["noprod"].filename, "/clusters/sandbox/baseline/README.md") &&
      endswith(local_file.cluster_admin_tool_values["prod:metrics"].filename, "/clusters/production/tools/metrics/values.yaml") &&
      yamldecode(local_file.cluster_admin_catalog["enabled"].content).clusters.prod == "production" &&
      oci_devops_deploy_environment.prod_oke_environment[0].display_name == "production"
    )
    error_message = "Cluster directories, catalogs and OCI environment labels must use configured names."
  }
  assert {
    condition = (
      yamldecode(base64decode(oci_devops_deploy_artifact.component_prod_values["invoice"].deploy_artifact_source[0].base64encoded_content)).environment == "live" &&
      yamldecode(base64decode(oci_devops_deploy_artifact.component_prod_values["invoice"].deploy_artifact_source[0].base64encoded_content)).environmentRole == "prod" &&
      yamldecode(base64decode(oci_devops_deploy_artifact.component_values["invoice:staging"].deploy_artifact_source[0].base64encoded_content)).environmentRole == "staging"
    )
    error_message = "Helm values must carry an independent environment name and workflow role."
  }
  assert {
    condition = (
      strcontains(base64decode(oci_devops_deploy_artifact.application_bootstrap_command_spec[0].deploy_artifact_source[0].base64encoded_content), "sandbox) target_cluster_id=") &&
      strcontains(base64decode(oci_devops_deploy_artifact.cluster_admin_decommission_command["enabled"].deploy_artifact_source[0].base64encoded_content), "production) cluster_id=")
    )
    error_message = "Bootstrap and decommission must resolve the renamed targets."
  }
}

run "build_only_ignores_delivery_names" {
  command = plan
  module { source = "./modules/devops" }
  variables {
    application_delivery_mode = "build_only"
    enable_cluster_admin      = false
    environment_names         = { dev = "development", staging = "uat", prod = "live" }
  }
  assert {
    condition = (
      length(oci_devops_deploy_pipeline.deploy_component) == 0 &&
      length(oci_devops_deploy_environment.oke_environment) == 0 &&
      length(oci_devops_build_pipeline.application_delivery) == 3
    )
    error_message = "Naming must not introduce deployment resources into build-only mode."
  }
}

run "cluster_only_with_custom_targets" {
  command = plan
  module { source = "./modules/devops" }
  variables {
    application_delivery_mode = "build_only"
    environment_names         = { noprod_cluster = "sandbox", prod_cluster = "live" }
    cluster_administration    = { tools = [] }
  }
  assert {
    condition = (
      length(oci_devops_deploy_pipeline.deploy_component) == 0 &&
      length(oci_devops_deploy_pipeline.cluster_admin) == 2 &&
      oci_devops_deploy_pipeline.cluster_admin["prod"].display_name == "cluster-admin-live" &&
      length(keys(yamldecode(local_file.cluster_admin_catalog["enabled"].content).tools)) == 0 &&
      keys(oci_devops_deploy_stage.cluster_admin_approval) == ["prod"]
    )
    error_message = "Independent cluster administration must support renamed targets and an empty tool catalog."
  }
}
