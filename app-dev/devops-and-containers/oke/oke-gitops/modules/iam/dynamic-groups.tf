data "oci_identity_domain" "devops_domain" {
  domain_id = var.iam_domain_id
}

locals {
  idcs_endpoint = data.oci_identity_domain.devops_domain.url
  matching_rule = <<EOT
  ANY { ALL {resource.type = 'devopsdeploypipeline', resource.compartment.id = '${var.compartment_id}'},
        ALL {resource.type = 'devopsrepository', resource.compartment.id = '${var.compartment_id}'},
        ALL {resource.type = 'devopsbuildpipeline',resource.compartment.id = '${var.compartment_id}'},
        ALL {resource.type = 'devopsconnection',resource.compartment.id = '${var.compartment_id}'}
  }
  EOT
}

resource "oci_identity_domains_dynamic_resource_group" "devOpsDynamicGroup" {
  display_name  = var.dynamic_group_name
  idcs_endpoint = local.idcs_endpoint
  description   = "Dynamic group for the OCI DevOps service"
  matching_rule = local.matching_rule
  schemas       = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]
}

