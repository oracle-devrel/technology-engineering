mock_provider "oci" {
  mock_data "oci_identity_region_subscriptions" {
    defaults = {
      region_subscriptions = [{
        region_name    = "eu-milan-1"
        region_key     = "MIL"
        is_home_region = true
      }]
    }
  }
  mock_data "oci_artifacts_container_configuration" {
    defaults = { namespace = "testnamespace" }
  }
  mock_data "oci_identity_tenancy" {
    defaults = { name = "testtenancy" }
  }
  mock_data "oci_identity_user" {
    defaults = { name = "manual-user" }
  }
}

mock_provider "oci" {
  alias = "home"
  mock_data "oci_identity_domain" {
    defaults = {
      display_name = "TestDomain"
      url          = "https://example.identity.oraclecloud.com"
    }
  }
}

mock_provider "local" {}
mock_provider "null" {}
mock_provider "time" {}
mock_provider "random" {}

variables {
  region                      = "eu-milan-1"
  tenancy_ocid                = "ocid1.tenancy.oc1..test"
  current_user_ocid           = "ocid1.user.oc1..test"
  compartment_ocid            = "ocid1.compartment.oc1..test"
  application_delivery_mode   = "build_only"
  auth_token                  = "mock-manual-token"
  oke_compartment_id          = "ocid1.compartment.oc1..test"
  prod_oke_compartment_id     = "ocid1.compartment.oc1..test"
  network_compartment_id      = "ocid1.compartment.oc1..test"
  prod_network_compartment_id = "ocid1.compartment.oc1..test"
  oke_cluster_id              = "ocid1.cluster.oc1.eu-milan-1.test"
  prod_oke_cluster_id         = "ocid1.cluster.oc1.eu-milan-1.test"
  oke_vcn_id                  = "ocid1.vcn.oc1.eu-milan-1.test"
  prod_oke_vcn_id             = "ocid1.vcn.oc1.eu-milan-1.test"
  oke_worker_subnet_id        = "ocid1.subnet.oc1.eu-milan-1.test"
  prod_oke_worker_subnet_id   = "ocid1.subnet.oc1.eu-milan-1.test"
}

run "manual_mode_preserved" {
  command = plan
  assert {
    condition     = length(oci_identity_domains_user.automation) == 0 && length(oci_kms_vault.credentials) == 0
    error_message = "Manual mode must not create credentials or Vault resources."
  }
  assert {
    condition     = local.effective_git_password == var.auth_token
    error_message = "Manual authentication must remain unchanged."
  }
}

run "native_complex_inputs" {
  command = plan
  variables {
    applications = [{ name = "shop", components = [{ name = "invoice" }, { name = "checkout" }] }]
    cluster_administration = {
      tools = [{ name = "keda", repository = "https://kedacore.github.io/charts", chart = "keda", version = "2.20.1" }]
    }
  }
  assert {
    condition     = local.application_count == 1 && local.component_count == 2
    error_message = "Native RM complex values must preserve application and component configuration."
  }
}

run "native_blank_optional_inputs" {
  command = plan
  variables {
    applications = [{
      name       = "shop", namespace = "", prod_namespace = null, chart_path = "", chart_version = "", chart_repository_name = "",
      components = [{ name = "invoice", build_spec_path = "", chart_version = "" }]
    }]
    cluster_administration = [{ name = "keda", repository = "https://kedacore.github.io/charts", chart = "keda", version = "2.20.1", namespace = "", depends_on = [""] }]
  }
  assert {
    condition     = !contains(keys(local.application_config[0]), "namespace") && !contains(keys(local.application_config[0].components[0]), "build_spec_path") && length(local.cluster_admin_config.tools[0].depends_on) == 0
    error_message = "Blank RM optional fields must behave like omitted values and use conventional defaults."
  }
}

run "automatic_build_only_without_iam" {
  command = plan
  variables {
    create_automatic_credentials = true
    automatic_credentials_email  = "automation@example.com"
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = "mock-manual-token"
  }
  assert {
    condition     = keys(oci_identity_domains_user.automation) == ["bootstrap"]
    error_message = "Build-only mode needs only the repository bootstrap user."
  }
  assert {
    condition     = local.effective_git_password == var.auth_token && local.effective_git_username == local.git_username
    error_message = "Automatic credentials must not replace user-supplied repository seeding credentials."
  }
  assert {
    condition     = length(oci_kms_vault.credentials) == 1 && length(oci_kms_key.credentials) == 1 && length(oci_vault_secret.automation) == 1
    error_message = "Automatic mode must create a Vault, key and token secret."
  }
  assert {
    condition     = length(oci_identity_policy.automation) == 1 && length(module.iam) == 0
    error_message = "Credential creation must create its access policy without enabling pipeline IAM."
  }
  assert {
    condition     = oci_identity_policy.automation[0].compartment_id == module.devops.devops_project_compartment_id && random_string.automation_policy_suffix[0].length == 7
    error_message = "The credential policy belongs to the DevOps project compartment with a stable seven-character random suffix."
  }
}

run "automatic_delivery_with_iam" {
  command = plan
  variables {
    application_delivery_mode    = "oci_devops"
    create_automatic_credentials = true
    automatic_credentials_email  = "automation@example.com"
    create_iam                   = true
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = "mock-manual-token"
    oke_compartment_id           = "ocid1.compartment.oc1..test"
    prod_oke_compartment_id      = "ocid1.compartment.oc1..test"
    network_compartment_id       = "ocid1.compartment.oc1..test"
    prod_network_compartment_id  = "ocid1.compartment.oc1..test"
    oke_cluster_id               = "ocid1.cluster.oc1.eu-milan-1.test"
    prod_oke_cluster_id          = "ocid1.cluster.oc1.eu-milan-1.prodtest"
    oke_vcn_id                   = "ocid1.vcn.oc1.eu-milan-1.test"
    prod_oke_vcn_id              = "ocid1.vcn.oc1.eu-milan-1.prodtest"
    oke_worker_subnet_id         = "ocid1.subnet.oc1.eu-milan-1.test"
    prod_oke_worker_subnet_id    = "ocid1.subnet.oc1.eu-milan-1.prodtest"
  }
  assert {
    condition     = keys(oci_identity_domains_user.automation) == ["bootstrap", "pull"]
    error_message = "Delivery requires separate bootstrap and read-only pull users."
  }
  assert {
    condition     = length(oci_identity_policy.automation) == 1 && length(module.iam) == 1
    error_message = "IAM-enabled automatic mode must create both policy sets."
  }
}

run "automatic_existing_project" {
  command = plan
  variables {
    create_devops_project        = false
    existing_devops_project_id   = "ocid1.devopsproject.oc1.eu-milan-1.existing"
    create_automatic_credentials = true
    automatic_credentials_email  = "automation@example.com"
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = "mock-manual-token"
  }
  override_data {
    target = module.devops.data.oci_devops_project.existing[0]
    values = {
      id             = "ocid1.devopsproject.oc1.eu-milan-1.existing"
      name           = "existing-project"
      compartment_id = "ocid1.compartment.oc1..existing"
    }
  }
  assert {
    condition     = local.credentials_compartment_id == "ocid1.compartment.oc1..existing"
    error_message = "Default credential placement must follow the actual reused project."
  }
  assert {
    condition     = startswith(local.credential_prefix, "existing-project-")
    error_message = "Account names must derive from the resolved project."
  }
}

run "reject_missing_account_email" {
  command = plan
  variables {
    create_automatic_credentials = true
    automatic_credentials_email  = ""
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = "mock-manual-token"
  }
  expect_failures = [oci_identity_domains_user.automation["bootstrap"]]
}

run "automatic_multiple_applications_and_operations" {
  command = plan
  variables {
    applications = jsonencode([
      { name = "shop", components = [{ name = "invoice" }, { name = "checkout" }] },
      { name = "orders", components = [{ name = "fulfillment" }] }
    ])
    application_delivery_mode            = "oci_devops"
    enable_cluster_admin                 = true
    create_automatic_credentials         = true
    automatic_credentials_email          = "automation@example.com"
    automatic_credentials_compartment_id = "ocid1.compartment.oc1..vault"
    create_iam                           = true
    devops_iam_domain_id                 = "ocid1.domain.oc1..test"
    auth_token                           = "mock-manual-token"
    oke_compartment_id                   = "ocid1.compartment.oc1..test"
    prod_oke_compartment_id              = "ocid1.compartment.oc1..test"
    network_compartment_id               = "ocid1.compartment.oc1..test"
    prod_network_compartment_id          = "ocid1.compartment.oc1..test"
    oke_cluster_id                       = "ocid1.cluster.oc1.eu-milan-1.test"
    prod_oke_cluster_id                  = "ocid1.cluster.oc1.eu-milan-1.test"
    oke_vcn_id                           = "ocid1.vcn.oc1.eu-milan-1.test"
    prod_oke_vcn_id                      = "ocid1.vcn.oc1.eu-milan-1.test"
    oke_worker_subnet_id                 = "ocid1.subnet.oc1.eu-milan-1.test"
    prod_oke_worker_subnet_id            = "ocid1.subnet.oc1.eu-milan-1.test"
  }
  assert {
    condition     = local.credentials_compartment_id == module.devops.devops_project_compartment_id
    error_message = "Legacy compartment overrides must not move credentials outside the DevOps project compartment."
  }
  assert {
    condition     = length(module.devops.repository_ids) == 7 && length(module.devops.bootstrap_pipeline_ids) == 2
    error_message = "Scopes must include shared, chart, source and operator repositories across all applications."
  }
}
run "reject_duplicate_application_environments" {
  command = plan
  variables { staging_environment_name = "dev" }
  expect_failures = [terraform_data.environment_names]
}

run "reject_duplicate_cluster_targets" {
  command = plan
  variables { noprod_cluster_name = "prod" }
  expect_failures = [terraform_data.environment_names]
}

run "reject_unsafe_environment_names" {
  command = plan
  variables { prod_environment_name = "../live" }
  expect_failures = [terraform_data.environment_names]
}

run "reject_empty_environment_names" {
  command = plan
  variables { dev_environment_name = "" }
  expect_failures = [terraform_data.environment_names]
}

run "reject_oversized_environment_names" {
  command = plan
  variables { prod_cluster_name = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyzabcdefghijkl" }
  expect_failures = [terraform_data.environment_names]
}

run "custom_environment_output" {
  command = plan
  variables {
    dev_environment_name     = "development"
    staging_environment_name = "uat"
    prod_environment_name    = "live"
    noprod_cluster_name      = "sandbox"
    prod_cluster_name        = "production"
  }
  assert {
    condition     = output.environment_names.dev == "development" && output.environment_names.prod == "live" && output.environment_names.noprod_cluster == "sandbox"
    error_message = "Outputs must expose configured names under stable workflow roles."
  }
}

run "reject_overlong_derived_release_name" {
  command = plan
  variables {
    application_delivery_mode = "oci_devops"
    dev_environment_name      = "abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz"
  }
  expect_failures = [terraform_data.environment_names]
}

run "reject_shared_cluster_release_collision" {
  command = plan
  variables {
    application_delivery_mode = "oci_devops"
    applications              = [{ name = "shop", components = [{ name = "shop" }] }]
  }
  expect_failures = [terraform_data.environment_names]
}
