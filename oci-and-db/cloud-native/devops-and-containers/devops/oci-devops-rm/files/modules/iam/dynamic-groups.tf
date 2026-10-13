data "oci_identity_domain" "devops_domain" {
  domain_id = var.iam_domain_id
}

locals {
  idcs_endpoint = data.oci_identity_domain.devops_domain.url

  matching_rule = "ANY {${join(", ", [for id in var.resource_ids : "resource.id = '${id}'"])}}"
}

resource "oci_identity_domains_dynamic_resource_group" "devops_dynamic_group" {
  display_name  = var.dynamic_group_name
  idcs_endpoint = local.idcs_endpoint
  description   = "Dynamic group for OCI DevOps resources created by the OKE Helm starter stack"
  matching_rule = local.matching_rule
  schemas       = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]

  lifecycle {
    ignore_changes = [schemas]
  }
}
