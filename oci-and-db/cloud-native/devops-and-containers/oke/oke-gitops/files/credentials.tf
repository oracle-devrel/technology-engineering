locals {
  credentials_compartment_id = module.devops.devops_project_compartment_id
  credential_prefix          = "${substr(replace(lower(module.devops.devops_project_name), "/[^a-z0-9._-]+/", "-"), 0, 60)}-gitops-${substr(sha256(module.devops.devops_project_id), 0, 8)}"
  credential_accounts = var.create_automatic_credentials ? {
    git  = "Read-only GitOps repositories"
    pull = "Read-only GitOps registry artifacts"
  } : {}
  credential_usernames = {
    for key, user in oci_identity_domains_user.automation : key =>
    "${key == "git" ? data.oci_identity_tenancy.current_tenancy.name : data.oci_artifacts_container_configuration.credentials[0].namespace}/${data.oci_identity_domain.credentials[0].display_name}/${user.user_name}"
  }
}

data "oci_identity_domain" "credentials" {
  count     = var.create_automatic_credentials ? 1 : 0
  provider  = oci.home
  domain_id = var.automation_iam_domain_id

  lifecycle {
    precondition {
      condition     = try(trimspace(var.automation_iam_domain_id) != "", false)
      error_message = "Select an Automation Identity Domain when creating OCI Vault and credentials."
    }
  }
}

data "oci_artifacts_container_configuration" "credentials" {
  count          = var.create_automatic_credentials ? 1 : 0
  compartment_id = var.tenancy_ocid
}

resource "oci_identity_domains_user" "automation" {
  for_each      = local.credential_accounts
  provider      = oci.home
  idcs_endpoint = data.oci_identity_domain.credentials[0].url
  schemas       = ["urn:ietf:params:scim:schemas:core:2.0:User", "urn:ietf:params:scim:schemas:oracle:idcs:extension:user:User", "urn:ietf:params:scim:schemas:oracle:idcs:extension:capabilities:User"]
  user_name     = "${local.credential_prefix}-${each.key}"
  display_name  = "${module.devops.devops_project_name}: ${each.value}"
  active        = true

  name {
    given_name  = module.devops.devops_project_name
    family_name = each.key
  }
  emails {
    value   = var.automatic_credentials_email
    type    = "work"
    primary = true
  }
  emails {
    value   = var.automatic_credentials_email
    type    = "recovery"
    primary = false
  }
  urnietfparamsscimschemasoracleidcsextensionuser_user {
    # Identity Domains service users cannot have OCI auth tokens.
    service_user        = false
    bypass_notification = true
  }
  urnietfparamsscimschemasoracleidcsextensioncapabilities_user {
    can_use_auth_tokens              = true
    can_use_api_keys                 = false
    can_use_console                  = false
    can_use_console_password         = false
    can_use_customer_secret_keys     = false
    can_use_db_credentials           = false
    can_use_oauth2client_credentials = false
    can_use_smtp_credentials         = false
  }
  lifecycle {
    ignore_changes = [schemas, urnietfparamsscimschemasoracleidcsextensionuser_user[0].bypass_notification]
    precondition {
      condition     = try(trimspace(var.automatic_credentials_email) != "", false)
      error_message = "automatic_credentials_email must not be empty."
    }
  }
}

resource "oci_identity_domains_group" "automation" {
  for_each       = local.credential_accounts
  provider       = oci.home
  idcs_endpoint  = data.oci_identity_domain.credentials[0].url
  attribute_sets = ["all"]
  schemas        = ["urn:ietf:params:scim:schemas:core:2.0:Group"]
  display_name   = "${local.credential_prefix}-${each.key}"
  members {
    value = oci_identity_domains_user.automation[each.key].id
    type  = "User"
  }
  lifecycle {
    ignore_changes = [schemas]
  }
}

resource "oci_identity_domains_auth_token" "automation" {
  for_each      = local.credential_accounts
  provider      = oci.home
  idcs_endpoint = data.oci_identity_domain.credentials[0].url
  schemas       = ["urn:ietf:params:scim:schemas:oracle:idcs:authToken"]
  description   = "${module.devops.devops_project_name}: ${each.value}"
  user {
    value = oci_identity_domains_user.automation[each.key].id
    ocid  = oci_identity_domains_user.automation[each.key].ocid
  }
  lifecycle {
    ignore_changes = [schemas]
  }
}

resource "oci_kms_vault" "credentials" {
  count          = var.create_automatic_credentials ? 1 : 0
  compartment_id = local.credentials_compartment_id
  display_name   = "${local.credential_prefix}-credentials"
  vault_type     = "DEFAULT"
}

# Fresh Vault endpoints can become ACTIVE before their KMS DNS records resolve.
resource "time_sleep" "credentials_vault_dns" {
  count           = var.create_automatic_credentials ? 1 : 0
  create_duration = "60s"
  triggers = {
    vault_id = oci_kms_vault.credentials[0].id
  }
}

resource "oci_kms_key" "credentials" {
  count               = var.create_automatic_credentials ? 1 : 0
  compartment_id      = local.credentials_compartment_id
  display_name        = "${local.credential_prefix}-credentials"
  management_endpoint = oci_kms_vault.credentials[0].management_endpoint
  depends_on          = [time_sleep.credentials_vault_dns]
  key_shape {
    algorithm = "AES"
    length    = 32
  }
}

resource "oci_vault_secret" "automation" {
  for_each       = local.credential_accounts
  compartment_id = local.credentials_compartment_id
  vault_id       = oci_kms_vault.credentials[0].id
  key_id         = oci_kms_key.credentials[0].id
  secret_name    = "${local.credential_prefix}-${each.key}-credentials"
  secret_content {
    content_type = "BASE64"
    content = sensitive(base64encode(jsonencode({
      username = local.credential_usernames[each.key]
      password = oci_identity_domains_auth_token.automation[each.key].token
    })))
  }
}

resource "random_string" "automation_policy_suffix" {
  count   = var.create_automatic_credentials ? 1 : 0
  length  = 7
  special = false
  upper   = false
}

resource "oci_identity_policy" "automation" {
  count          = var.create_automatic_credentials ? 1 : 0
  provider       = oci.home
  compartment_id = local.credentials_compartment_id
  name           = "${substr(replace(lower(module.devops.devops_project_name), "/[^a-z0-9._-]+/", "-"), 0, 60)}-gitops-credentials-${random_string.automation_policy_suffix[0].result}"
  description    = "Read-only GitOps repository and registry access"
  statements = [
    "Allow group id ${oci_identity_domains_group.automation["git"].ocid} to read devops-project in compartment id ${local.credentials_compartment_id} where target.project.id = '${module.devops.devops_project_id}'",
    "Allow group id ${oci_identity_domains_group.automation["git"].ocid} to read devops-repository in compartment id ${local.credentials_compartment_id} where any {${join(", ", [for id in module.devops.gitops_repository_ids : "target.repository.id = '${id}'"])}}",
    "Allow group id ${oci_identity_domains_group.automation["pull"].ocid} to read repos in compartment id ${local.credentials_compartment_id} where target.repo.name = /${replace(var.ocir_repo_path_prefix, "/", "\\/")}\\/*/"
  ]
  lifecycle {
    precondition {
      condition     = can(regex("^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$", var.ocir_repo_path_prefix))
      error_message = "ocir_repo_path_prefix must be a lowercase registry path without wildcards."
    }
  }
}
