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

variables {
  region                    = "eu-milan-1"
  tenancy_ocid              = "ocid1.tenancy.oc1..test"
  current_user_ocid         = "ocid1.user.oc1..test"
  compartment_ocid          = "ocid1.compartment.oc1..test"
  application_delivery_mode = "build_only"
  auth_token                = "mock-manual-token"
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

run "automatic_build_only_without_iam" {
  command = plan
  variables {
    create_automatic_credentials = true
    automatic_credentials_email  = "automation@example.com"
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = null
  }
  assert {
    condition     = keys(oci_identity_domains_user.automation) == ["bootstrap"]
    error_message = "Build-only mode needs only the repository bootstrap user."
  }
  assert {
    condition     = length(oci_kms_vault.credentials) == 1 && length(oci_kms_key.credentials) == 1 && length(oci_vault_secret.automation) == 1
    error_message = "Automatic mode must create a Vault, key and token secret."
  }
  assert {
    condition     = length(oci_identity_policy.automation) == 0 && length(module.iam) == 0
    error_message = "Credential creation must not force IAM creation."
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
    auth_token                   = null
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
    auth_token                   = null
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
    devops_iam_domain_id         = "ocid1.domain.oc1..test"
    auth_token                   = null
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
    auth_token                           = null
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
    condition     = local.credentials_compartment_id == "ocid1.compartment.oc1..vault"
    error_message = "Explicit credential placement must override the project compartment."
  }
  assert {
    condition     = length(module.devops.repository_ids) == 7 && length(module.devops.bootstrap_pipeline_ids) == 2
    error_message = "Scopes must include shared, chart, source and operator repositories across all applications."
  }
}
