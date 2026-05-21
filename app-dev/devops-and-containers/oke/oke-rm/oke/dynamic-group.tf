
data "oci_identity_domain" "karpenter_domain" {
  domain_id = var.karpenter_iam_domain_id
  count     = var.create_karpenter_policies ? 1 : 0
}

locals {
  karpenter_matching_rule = <<EOT
  ANY { ALL {instance.compartment.id = '${var.oke_compartment_id}'}
  }
  EOT
}


resource "oci_identity_domains_dynamic_resource_group" "karpenter_dynamic_group" {
  display_name  = var.karpenter_dynamic_group_name
  idcs_endpoint = data.oci_identity_domain.karpenter_domain.0.url
  description   = "Dynamic group for Karpenter to provision instances on the cluster ${var.cluster_name}"
  matching_rule = local.karpenter_matching_rule
  schemas       = ["urn:ietf:params:scim:schemas:oracle:idcs:DynamicResourceGroup"]
  count         = var.create_karpenter_policies ? 1 : 0
}