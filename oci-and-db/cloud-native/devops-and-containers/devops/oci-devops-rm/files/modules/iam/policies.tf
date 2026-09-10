locals {
  network_compartment_ids = var.enable_oke_access ? distinct(compact([
    var.network_compartment_id,
    var.prod_network_compartment_id
  ])) : []

  oke_compartment_ids = var.enable_oke_access ? distinct(compact([
    var.oke_compartment_id,
    var.prod_oke_compartment_id
  ])) : []

  default_statements = [
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage devops-family in compartment id ${var.compartment_id}",
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage repos in compartment id ${var.compartment_id}",
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage ons-topics in compartment id ${var.compartment_id}",
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage logging-family in compartment id ${var.compartment_id}",
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage all-artifacts in compartment id ${var.compartment_id}",
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage compute-container-family in compartment id ${var.compartment_id}"
  ]

  secret_statements = [
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to read secret-family in compartment id ${var.secret_compartment_id}"
  ]

  oke_statements = [
    for compartment_id in local.oke_compartment_ids :
    "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to manage cluster in compartment id ${compartment_id}"
  ]

  network_statements = flatten([
    for compartment_id in local.network_compartment_ids : [
      "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to use subnets in compartment id ${compartment_id}",
      "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to use vnics in compartment id ${compartment_id}",
      "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to use dhcp-options in compartment id ${compartment_id}",
      "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.devops_dynamic_group.ocid} to use network-security-groups in compartment id ${compartment_id}"
    ]
  ])

  statements = concat(
    local.default_statements,
    local.oke_statements,
    local.network_statements
  )
}

resource "oci_identity_policy" "devops_policy" {
  compartment_id = var.compartment_id
  description    = "Policies for the OKE Helm starter OCI DevOps resources"
  name           = var.devops_policy_name
  statements     = local.statements
}

resource "oci_identity_policy" "devops_secret_access_policy" {
  count = var.enable_secret_access ? 1 : 0

  compartment_id = var.secret_compartment_id
  description    = "Vault secret access for the OKE DevOps starter pipelines"
  name           = "${var.devops_policy_name}-secret-access"
  statements     = local.secret_statements
}
