mock_provider "oci" {
  mock_data "oci_identity_domain" {
    defaults = { url = "https://example.identity.oraclecloud.com" }
  }
}

variables {
  compartment_id              = "ocid1.compartment.oc1..project"
  policy_compartment_id       = "ocid1.tenancy.oc1..test"
  network_compartment_id      = "ocid1.compartment.oc1..network"
  oke_compartment_id          = "ocid1.compartment.oc1..oke"
  iam_domain_id               = "ocid1.domain.oc1..test"
  dynamic_group_name          = "TestBuild"
  devops_policy_name          = "test-gitops"
  project_id                  = "ocid1.devopsproject.oc1..selected"
  build_pipeline_ids          = ["ocid1.devopsbuildpipeline.oc1..mirror", "ocid1.devopsbuildpipeline.oc1..bootstrap"]
  bootstrap_pipeline_id       = "ocid1.devopsbuildpipeline.oc1..bootstrap"
  deploy_pipeline_id          = "ocid1.devopsdeploypipeline.oc1..install"
  pipelines_repository_id     = "ocid1.devopsrepository.oc1..pipelines"
  deploy_environment_id       = "ocid1.devopsdeployenvironment.oc1..oke"
  deploy_artifact_ids         = ["ocid1.devopsdeployartifact.oc1..chart", "ocid1.devopsdeployartifact.oc1..values", "ocid1.devopsdeployartifact.oc1..prepare"]
  oke_cluster_id              = "ocid1.cluster.oc1..selected"
  ocir_repo_path_prefix       = "company-name/org"
  use_network_security_groups = false
  secret_ids                  = []
}

run "manual_empty_allowlist" {
  command = apply
  module { source = "./modules/iam" }

  assert {
    condition     = output.build_matching_rule == "ANY {ALL {resource.type = 'devopsbuildpipeline', resource.id = 'ocid1.devopsbuildpipeline.oc1..mirror'}, ALL {resource.type = 'devopsbuildpipeline', resource.id = 'ocid1.devopsbuildpipeline.oc1..bootstrap'}}" && output.deployment_matching_rule == "ALL {resource.type = 'devopsdeploypipeline', resource.id = 'ocid1.devopsdeploypipeline.oc1..install'}"
    error_message = "Membership must include only the two exact builds and the exact installer."
  }
  assert {
    condition     = !can(regex("resource.compartment|devopsrepository|devopsconnection|devopsdeployenvironment", "${output.build_matching_rule} ${output.bootstrap_matching_rule} ${output.deployment_matching_rule}"))
    error_message = "Unrelated compartment resources must never enter any execution group."
  }
  assert {
    condition     = length(local.secret_statements) == 0 && !can(regex("secret-bundles|clusters|subnets|vnics|compute-container", join("\n", local.build_statements)))
    error_message = "Manual empty allowlist grants no secrets; builds have no direct install permissions."
  }
  assert {
    condition     = alltrue([for statement in output.statements : !can(regex("all-artifacts|ons-topics|REPOSITORY_MANAGE|REPOSITORY_DELETE|CLUSTER_CREATE|CLUSTER_DELETE|CLUSTER_UPDATE|INSTANCE_MOVE", statement))])
    error_message = "DevOps family management must not widen registry, secrets, cluster, network, or container-instance permissions."
  }
  assert {
    condition = length([for statement in output.statements : statement if strcontains(statement, "devops-family")]) == 2 && toset([for statement in output.statements : statement if strcontains(statement, "devops-family")]) == toset([
      "Allow dynamic-group id ${output.principals.bootstrap_dynamic_group_id} to manage devops-family in compartment id ocid1.compartment.oc1..project",
      "Allow dynamic-group id ${output.principals.deployment_dynamic_group_id} to manage devops-family in compartment id ocid1.compartment.oc1..project"
    ])
    error_message = "Exactly the bootstrap and installer groups may manage devops-family, only in the actual project compartment, not the policy, OKE, or network compartment."
  }
  assert {
    condition     = length([for statement in local.build_statements : statement if strcontains(statement, "inspect repos in compartment id ocid1.compartment.oc1..project") && !strcontains(statement, "target.repo.name")]) == 1
    error_message = "Registry configuration and filtered list require inspect access without name context."
  }
  assert {
    condition     = length([for statement in local.build_statements : statement if strcontains(statement, "manage repos") && strcontains(statement, "target.repo.name = /company-name\\/org\\/*/") && strcontains(statement, "REPOSITORY_CREATE") && strcontains(statement, "REPOSITORY_UPDATE") && strcontains(statement, "REPOSITORY_READ")]) == 1
    error_message = "Build registry writes must be push-only and prefix bounded."
  }
  assert {
    condition     = length([for statement in local.deploy_statements : statement if strcontains(statement, "read repos") && endswith(statement, "target.repo.name = /company-name\\/org\\/*/")]) == 1
    error_message = "Installer registry reads must escape internal and boundary slashes without widening the prefix."
  }
  assert {
    condition     = length(local.bootstrap_statements) == 1 && local.bootstrap_statements[0] == "Allow dynamic-group id ${output.principals.bootstrap_dynamic_group_id} to manage devops-family in compartment id ocid1.compartment.oc1..project"
    error_message = "Bootstrap must use one project-compartment DevOps family grant, without the old pipeline or operation conditions."
  }
  assert {
    condition     = output.bootstrap_matching_rule == "ALL {resource.type = 'devopsbuildpipeline', resource.id = 'ocid1.devopsbuildpipeline.oc1..bootstrap'}" && oci_identity_domains_dynamic_resource_group.bootstrap.display_name == "TestBuild-bootstrap"
    error_message = "The bootstrap-trigger group must contain only the exact bootstrap build pipeline."
  }
  assert {
    condition     = length(local.deploy_statements) == 5 && length([for statement in local.deploy_statements : statement if strcontains(statement, "devops-")]) == 1 && local.deploy_statements[0] == "Allow dynamic-group id ${output.principals.deployment_dynamic_group_id} to manage devops-family in compartment id ocid1.compartment.oc1..project"
    error_message = "Installer must replace its five granular DevOps grants with one project-compartment family grant while retaining the four scoped OCI grants."
  }
  assert {
    condition = toset(local.build_statements) == toset([
      "Allow dynamic-group id ${output.principals.build_dynamic_group_id} to read devops-project in compartment id ocid1.compartment.oc1..project where target.project.id = 'ocid1.devopsproject.oc1..selected'",
      "Allow dynamic-group id ${output.principals.build_dynamic_group_id} to read devops-repository in compartment id ocid1.compartment.oc1..project where target.repository.id = 'ocid1.devopsrepository.oc1..pipelines'",
      "Allow dynamic-group id ${output.principals.build_dynamic_group_id} to inspect repos in compartment id ocid1.compartment.oc1..project",
      "Allow dynamic-group id ${output.principals.build_dynamic_group_id} to manage repos in compartment id ocid1.compartment.oc1..project where all {target.repo.name = /company-name\\/org\\/*/, any {request.permission = 'REPOSITORY_READ', request.permission = 'REPOSITORY_CREATE', request.permission = 'REPOSITORY_UPDATE'}}"
    ]) && length(local.build_statements) == 4 && !can(regex("devops-family|devops-deploy", join("\n", local.build_statements)))
    error_message = "The shared build/mirror group must retain exactly its project/source reads and bounded registry permissions, without DevOps family or deployment grants."
  }
  assert {
    condition     = length([for statement in local.build_statements : statement if strcontains(statement, "read devops-repository") && strcontains(statement, "target.repository.id = 'ocid1.devopsrepository.oc1..pipelines'")]) == 1 && !can(regex("devops-repository|manage repos", join("\n", local.deploy_statements)))
    error_message = "Build source has one explicit repository grant; installer has no separate Git grants and no OCIR registry write grants."
  }
  assert {
    condition     = length([for statement in local.deploy_statements : statement if strcontains(statement, "manage clusters") && strcontains(statement, "target.cluster.id = 'ocid1.cluster.oc1..selected'") && strcontains(statement, "CLUSTER_MANAGE")]) == 1 && length(local.network_statements) == 3
    error_message = "Cluster administration is exact-cluster scoped; NSG permission is absent when unused."
  }
}

run "explicit_secrets_and_nsg" {
  command = apply
  module { source = "./modules/iam" }
  variables {
    secret_ids                  = ["ocid1.vaultsecret.oc1..git", "ocid1.vaultsecret.oc1..pull"]
    use_network_security_groups = true
  }
  assert {
    condition     = length(local.secret_statements) == 1 && strcontains(local.secret_statements[0], "target.secret.id = 'ocid1.vaultsecret.oc1..git'") && strcontains(local.secret_statements[0], "target.secret.id = 'ocid1.vaultsecret.oc1..pull'") && !strcontains(local.secret_statements[0], "build_dynamic_group_id") && length(local.network_statements) == 4
    error_message = "Only the two allowlisted secrets and configured network types may be granted."
  }
  assert {
    condition     = startswith(local.secret_statements[0], "Allow dynamic-group id ${output.principals.deployment_dynamic_group_id} to read secret-bundles")
    error_message = "Only the installation principal may read credential secrets."
  }
}

run "reject_registry_wildcard" {
  command = plan
  module { source = "./modules/iam" }
  variables { ocir_repo_path_prefix = "gitops/*" }
  expect_failures = [var.ocir_repo_path_prefix]
}

run "reject_secret_policy_injection" {
  command = plan
  module { source = "./modules/iam" }
  variables { secret_ids = ["ocid1.vaultsecret.oc1..git' OR 'x"] }
  expect_failures = [var.secret_ids]
}
