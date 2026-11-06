data "oci_identity_domain" "devops_domain" {
  domain_id = var.iam_domain_id
}

locals {
  idcs_endpoint = data.oci_identity_domain.devops_domain.url
  matching_rule = "ANY {${join(", ", [for id in var.build_pipeline_ids : "ALL {resource.type = 'devopsbuildpipeline', resource.id = '${id}'}"])}}"
}

resource "oci_identity_domains_dynamic_resource_group" "devOpsDynamicGroup" {
  attribute_sets = ["all"]
  display_name   = var.dynamic_group_name
  idcs_endpoint  = local.idcs_endpoint
  description    = "Only this stack's mirror and bootstrap build pipelines"
  matching_rule  = local.matching_rule
  schemas        = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]

  lifecycle {
    # OCI may add schema extensions such as OCITags after creation.
    ignore_changes = [schemas]
  }
}

resource "oci_identity_domains_dynamic_resource_group" "bootstrap" {
  attribute_sets = ["all"]
  display_name   = "${var.dynamic_group_name}-bootstrap"
  idcs_endpoint  = local.idcs_endpoint
  description    = "Only this stack's bootstrap build pipeline may trigger installation"
  matching_rule  = "ALL {resource.type = 'devopsbuildpipeline', resource.id = '${var.bootstrap_pipeline_id}'}"
  schemas        = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]

  lifecycle {
    ignore_changes = [schemas]
  }
}

resource "oci_identity_domains_dynamic_resource_group" "deployment" {
  attribute_sets = ["all"]
  display_name   = "${var.dynamic_group_name}-deployment"
  idcs_endpoint  = local.idcs_endpoint
  description    = "Only this stack's GitOps installation pipeline"
  matching_rule  = "ALL {resource.type = 'devopsdeploypipeline', resource.id = '${var.deploy_pipeline_id}'}"
  schemas        = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]

  lifecycle {
    ignore_changes = [schemas]
  }
}
