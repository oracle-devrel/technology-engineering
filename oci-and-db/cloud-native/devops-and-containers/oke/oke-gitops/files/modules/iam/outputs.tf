output "build_matching_rule" {
  value = oci_identity_domains_dynamic_resource_group.devOpsDynamicGroup.matching_rule
}

output "deployment_matching_rule" {
  value = oci_identity_domains_dynamic_resource_group.deployment.matching_rule
}

output "bootstrap_matching_rule" {
  value = oci_identity_domains_dynamic_resource_group.bootstrap.matching_rule
}

output "statements" {
  value = oci_identity_policy.devops_policy.statements
}

output "principals" {
  value = {
    build_dynamic_group_id      = oci_identity_domains_dynamic_resource_group.devOpsDynamicGroup.ocid
    bootstrap_dynamic_group_id  = oci_identity_domains_dynamic_resource_group.bootstrap.ocid
    deployment_dynamic_group_id = oci_identity_domains_dynamic_resource_group.deployment.ocid
    policy_id                   = oci_identity_policy.devops_policy.id
  }
}
