locals {
  default_statements = [
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to manage repos in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to manage devops-family in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to use ons-topics in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to read all-artifacts in compartment id ${var.compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to manage cluster in compartment id ${var.oke_compartment_id}"
  ]

  network_compartment_id = var.network_compartment_id == null ? "" : var.network_compartment_id
  network_statements = var.is_oke_cluster_private ? [
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to use subnets in compartment id ${local.network_compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to use vnics in compartment id ${local.network_compartment_id}",
    "Allow dynamic-group ${var.domain_name}/${var.dynamic_group_name} to use network-security-groups in compartment id ${local.network_compartment_id}"
  ] : []

  statements = concat(local.default_statements, local.network_statements)
}



resource "oci_identity_policy" "devops_policy" {
  compartment_id = var.compartment_id
  description    = "Policies for the OCI DevOps service in the compartment"
  name           = var.devops_policy_name
  statements = local.statements
}