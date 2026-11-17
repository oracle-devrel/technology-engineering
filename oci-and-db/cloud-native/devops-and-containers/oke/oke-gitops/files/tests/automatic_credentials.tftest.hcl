mock_provider "oci" {
  mock_data "oci_identity_region_subscriptions" {
    defaults = {
      region_subscriptions = [{
        region_name = "eu-amsterdam-1", region_key = "AMS", is_home_region = true
      }]
    }
  }
  mock_data "oci_identity_tenancy" {
    defaults = { name = "testtenancy" }
  }
  mock_data "oci_identity_user" {
    defaults = { name = "Default/manual-user" }
  }
  mock_data "oci_artifacts_container_configuration" {
    defaults = { namespace = "testnamespace" }
  }
}
mock_provider "oci" {
  alias = "home"
  mock_data "oci_identity_domain" {
    defaults = { display_name = "TestDomain", url = "https://example.identity.oraclecloud.com" }
  }
}
mock_provider "local" {}
mock_provider "null" {}
mock_provider "time" {}
mock_provider "random" {}

variables {
  region                    = "eu-amsterdam-1"
  tenancy_ocid              = "ocid1.tenancy.oc1..test"
  current_user_ocid         = "ocid1.user.oc1..test"
  compartment_ocid          = "ocid1.compartment.oc1..test"
  devops_compartment_id     = "ocid1.compartment.oc1..devops"
  oke_compartment_id        = "ocid1.compartment.oc1..oke"
  network_compartment_id    = "ocid1.compartment.oc1..network"
  oke_cluster_id            = "ocid1.cluster.oc1.eu-amsterdam-1.test"
  oke_worker_subnet_id      = "ocid1.subnet.oc1.eu-amsterdam-1.test"
  auth_token                = "mock-seeding-token"
  create_notification_topic = true
}

run "manual_flux_preserved" {
  command = plan
  variables {
    gitops_agent = "fluxcd"
    gitops_scope = "applications_and_cluster"
  }
  assert {
    condition     = length(oci_identity_domains_user.automation) == 0 && length(oci_kms_vault.credentials) == 0 && output.automatic_credentials == null
    error_message = "Manual mode must not create credential resources."
  }
}

run "automatic_flux_without_execution_iam" {
  command = plan
  variables {
    gitops_agent                 = "fluxcd"
    gitops_scope                 = "applications_and_cluster"
    create_automatic_credentials = true
    automation_iam_domain_id     = "ocid1.domain.oc1..automation"
  }
  assert {
    condition     = keys(oci_identity_domains_user.automation) == ["git", "pull"] && length(oci_identity_domains_auth_token.automation) == 2 && length(oci_vault_secret.automation) == 2
    error_message = "Automatic mode needs separate Git and OCIR users, tokens and secrets."
  }
  assert {
    condition     = length(oci_identity_policy.automation) == 1 && length(module.iam) == 0
    error_message = "Runtime account policies must be independent of execution IAM."
  }
  assert {
    condition     = oci_kms_vault.credentials[0].compartment_id == "ocid1.compartment.oc1..devops" && oci_kms_key.credentials[0].compartment_id == "ocid1.compartment.oc1..devops" && oci_identity_policy.automation[0].compartment_id == "ocid1.compartment.oc1..devops"
    error_message = "Vault, key and runtime policy must use the DevOps project compartment."
  }
  assert {
    condition     = random_string.automation_policy_suffix[0].length == 7 && time_sleep.credentials_vault_dns[0].create_duration == "60s"
    error_message = "Preserve stable unique policy naming and Vault DNS readiness."
  }
  assert {
    condition     = length(module.devops.gitops_repository_ids) == 2
    error_message = "Default runtime scope must include cluster-config and apps-config only."
  }
}

run "automatic_argocd_admin_fleet_with_execution_iam" {
  command = plan
  override_resource {
    override_during = plan
    target          = oci_identity_domains_group.automation["pull"]
    values          = { ocid = "ocid1.group.oc1..pull" }
  }
  variables {
    gitops_agent                 = "argocd"
    gitops_scope                 = "cluster_admin"
    enable_multicluster          = true
    create_automatic_credentials = true
    automation_iam_domain_id     = "ocid1.domain.oc1..automation"
    create_iam                   = true
    devops_iam_domain_id         = "ocid1.domain.oc1..execution"
  }
  assert {
    condition     = length(module.devops.gitops_repository_ids) == 2 && length(module.iam) == 1 && length(oci_identity_policy.automation) == 1
    error_message = "Argo CD admin fleets need cluster and fleet access plus independent policy sets."
  }
  assert {
    condition     = endswith(oci_identity_policy.automation[0].statements[2], "target.repo.name = /company-name\\/org\\/*/")
    error_message = "Runtime pull policy must escape internal and boundary slashes while preserving the exact prefix."
  }
}

run "automatic_flux_application_fleet" {
  command = plan
  variables {
    gitops_agent                 = "fluxcd"
    gitops_scope                 = "applications_and_cluster"
    enable_multicluster          = true
    create_automatic_credentials = true
    automation_iam_domain_id     = "ocid1.domain.oc1..automation"
  }
  assert {
    condition     = length(module.devops.gitops_repository_ids) == 3
    error_message = "Application fleets need cluster, application and fleet repository access."
  }
}

run "automatic_existing_project_uses_actual_compartment" {
  command = plan
  variables {
    create_devops_project        = false
    existing_devops_project_id   = "ocid1.devopsproject.oc1.eu-amsterdam-1.existing"
    create_automatic_credentials = true
    automation_iam_domain_id     = "ocid1.domain.oc1..automation"
  }
  override_data {
    target = module.devops.data.oci_devops_project.existing[0]
    values = {
      id = "ocid1.devopsproject.oc1.eu-amsterdam-1.existing", name = "existing-project", compartment_id = "ocid1.compartment.oc1..existing"
    }
  }
  assert {
    condition     = local.credentials_compartment_id == "ocid1.compartment.oc1..existing" && startswith(local.credential_prefix, "existing-project-gitops-")
    error_message = "Credential placement and naming must follow the reused project, not input defaults."
  }
}

run "reject_missing_automation_domain" {
  command = plan
  variables {
    create_automatic_credentials = true
  }
  expect_failures = [data.oci_identity_domain.credentials[0]]
}

run "execution_iam_without_automatic_credentials" {
  command = plan
  variables {
    create_iam           = true
    devops_iam_domain_id = "ocid1.domain.oc1..execution"
  }
  assert {
    condition     = length(module.iam) == 1 && length(oci_vault_secret.automation) == 0
    error_message = "Execution IAM must remain independent of automatic runtime credentials."
  }
}

run "new_stack_defaults" {
  command = plan
  assert {
    condition     = var.ocir_repo_path_prefix == "company-name/org"
    error_message = "New stacks must use a company/organization registry prefix."
  }
  assert {
    condition     = var.gitops_agent == "argocd" && var.gitops_scope == "cluster_admin" && !var.development_overwrite_repositories
    error_message = "New stacks must default to Argo CD, cluster administration only, and preserved customer repositories."
  }
  assert {
    condition     = length(module.devops.gitops_repository_ids) == 1 && output.apps_config_repository_url == null
    error_message = "Default stacks must not create the application repository."
  }
}
