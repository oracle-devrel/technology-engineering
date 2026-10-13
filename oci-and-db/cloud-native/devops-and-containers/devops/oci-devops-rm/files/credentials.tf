locals {
  credentials_compartment_id = coalesce(var.automatic_credentials_compartment_id, module.devops.devops_project_compartment_id)
  credential_prefix          = "${replace(lower(module.devops.devops_project_name), "/[^a-z0-9._-]+/", "-")}-${substr(sha256(module.devops.devops_project_id), 0, 8)}"
  credential_accounts = var.create_automatic_credentials ? merge(
    { bootstrap = "Repository bootstrap" },
    local.application_delivery_enabled ? { pull = "Read-only OCIR image pull" } : {}
  ) : {}
  credential_usernames = {
    for key, user in oci_identity_domains_user.automation : key =>
    "${data.oci_artifacts_container_configuration.credentials[0].namespace}/${data.oci_identity_domain.credentials[0].display_name}/${user.user_name}"
  }
  effective_git_username = var.create_automatic_credentials ? "${data.oci_identity_tenancy.current_tenancy.name}/${data.oci_identity_domain.credentials[0].display_name}/${oci_identity_domains_user.automation["bootstrap"].user_name}" : local.git_username
  effective_git_password = var.create_automatic_credentials ? sensitive(oci_identity_domains_auth_token.automation["bootstrap"].token) : var.auth_token
}

data "oci_identity_domain" "credentials" {
  count     = var.create_automatic_credentials ? 1 : 0
  provider  = oci.home
  domain_id = var.devops_iam_domain_id
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
    # Notification suppression is a write-only creation option, not user state.
    ignore_changes = [schemas, urnietfparamsscimschemasoracleidcsextensionuser_user[0].bypass_notification]
    precondition {
      condition     = trimspace(var.automatic_credentials_email) != ""
      error_message = "automatic_credentials_email is required when creating service accounts."
    }
  }
}

resource "oci_identity_domains_group" "automation" {
  for_each      = local.credential_accounts
  provider      = oci.home
  idcs_endpoint = data.oci_identity_domain.credentials[0].url
  # Group members are request-only attributes in Identity Domains reads.
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

# Use the selected domain endpoint; classic IAM cannot address every domain user.
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

# Fresh Vaults can become ACTIVE before their dedicated KMS DNS records resolve.
resource "time_sleep" "credentials_vault_dns" {
  count           = var.create_automatic_credentials ? 1 : 0
  create_duration = "120s"
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
  secret_name    = "${local.credential_prefix}-${each.key}-auth-token"

  secret_content {
    content_type = "BASE64"
    content      = sensitive(base64encode(oci_identity_domains_auth_token.automation[each.key].token))
  }
}

resource "oci_identity_policy" "automation" {
  count          = var.create_automatic_credentials && var.create_iam ? 1 : 0
  provider       = oci.home
  compartment_id = coalesce(var.iam_policy_compartment_id, var.tenancy_ocid)
  name           = "${local.credential_prefix}-credential-access"
  description    = "Repository bootstrap and read-only image pull permissions"
  statements = concat(
    [
      "Allow group id ${oci_identity_domains_group.automation["bootstrap"].ocid} to use devops-repository in compartment id ${module.devops.devops_project_compartment_id} where any {${join(", ", [for id in module.devops.repository_ids : "target.repository.id = '${id}'"])}}"
    ],
    local.application_delivery_enabled ? [
      "Allow group id ${oci_identity_domains_group.automation["pull"].ocid} to read repos in compartment id ${module.devops.devops_project_compartment_id} where any {${join(", ", [for repository in values(module.devops.component_image_repositories) : "target.repo.name = '${join("/", slice(split("/", repository), 2, length(split("/", repository))))}'"])}}"
    ] : []
  )
}
