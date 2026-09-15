output "cluster_id" {
  value = module.oke.cluster_id

  precondition {
    condition     = var.cni_type == "flannel" || (var.pod_subnet_id != null && var.pod_nsg_id != null)
    error_message = "pod_subnet_id and pod_nsg_id are required when cni_type is vcn_native."
  }

  precondition {
    condition     = var.cluster_kms_key_id == null || (var.kms_compartment_id != null && var.oke_vault_id != null)
    error_message = "kms_compartment_id and oke_vault_id are required when cluster_kms_key_id is set."
  }

  precondition {
    condition     = !var.enable_oidc_authentication || (var.oidc_issuer != null && var.oidc_client_id != null)
    error_message = "oidc_issuer and oidc_client_id are required when OIDC authentication is enabled."
  }

  precondition {
    condition     = !var.create_karpenter_policies || var.cluster_type == "enhanced"
    error_message = "Karpenter policies are available only for enhanced clusters."
  }

  precondition {
    condition     = !var.create_autoscaler_policies || var.cluster_type == "enhanced"
    error_message = "Cluster Autoscaler workload identity policies are available only for enhanced clusters."
  }
}

output "worker_pools" {
  value = module.oke.worker_pools
}

output "oidc_discovery_endpoint" {
  value = module.oke.cluster_oidc_discovery_endpoint
}

output "policy_statements" {
  description = "Flat list of all generated policy statements. Use policy_statements_by_feature for statement provenance."
  value = var.enable_policies ? distinct(concat(
    local.policy_statements_by_feature.cross_compartment_cni.compute,
    local.policy_statements_by_feature.cross_compartment_cni.network,
    local.compute_statements,
    local.network_statements,
    local.storage_statements,
    local.tag_statements,
    local.kms_statements,
    local.iam_statements
  )) : []
}

output "policy_statements_by_feature" {
  description = "Generated policy statements grouped by OKE feature and target scope."
  value       = var.enable_policies ? local.policy_statements_by_feature : null
}

output "policy_resources" {
  description = "OCI IAM policies created by the stack, including their compartment, OCID, and contributing feature."
  value = merge(
    local.create_cross_compartment_compute_policy ? {
      cross_compartment_compute = {
        name           = oci_identity_policy.oke_policy_cross_compartment_compute[0].name
        compartment_id = var.oke_compartment_id
        ocid           = oci_identity_policy.oke_policy_cross_compartment_compute[0].id
        features       = ["cross_compartment_cni"]
      }
    } : {},
    local.create_cross_compartment_network_policy ? {
      cross_compartment_network = {
        name           = oci_identity_policy.oke_policy_cross_compartment_network[0].name
        compartment_id = var.network_compartment_id
        ocid           = oci_identity_policy.oke_policy_cross_compartment_network[0].id
        features       = ["cross_compartment_cni"]
      }
    } : {},
    local.create_compute_policy ? {
      compute = {
        name           = oci_identity_policy.oke_policy_compute[0].name
        compartment_id = var.oke_compartment_id
        ocid           = oci_identity_policy.oke_policy_compute[0].id
        features       = compact([local.create_autoscaler_policies ? "autoscaler" : "", local.create_karpenter_policies ? "karpenter" : ""])
      }
    } : {},
    local.create_network_policy ? {
      network = {
        name           = oci_identity_policy.oke_policy_network[0].name
        compartment_id = var.network_compartment_id
        ocid           = oci_identity_policy.oke_policy_network[0].id
        features       = compact([length(local.autoscaler_network_statements) > 0 ? "autoscaler" : "", local.create_karpenter_policies ? "karpenter" : ""])
      }
    } : {},
    local.create_storage_policy ? {
      storage = {
        name           = oci_identity_policy.oke_policy_storage[0].name
        compartment_id = var.oke_compartment_id
        ocid           = oci_identity_policy.oke_policy_storage[0].id
        features       = ["karpenter"]
      }
    } : {},
    local.create_tag_policy ? {
      tag = {
        name           = oci_identity_policy.oke_policy_tag[0].name
        compartment_id = local.tag_compartment_id
        ocid           = oci_identity_policy.oke_policy_tag[0].id
        features       = ["karpenter"]
      }
    } : {},
    local.create_iam_policy ? {
      iam = {
        name           = oci_identity_policy.oke_policy_iam[0].name
        compartment_id = var.tenancy_ocid
        ocid           = oci_identity_policy.oke_policy_iam[0].id
        features       = ["karpenter"]
      }
    } : {},
    local.create_kms_policy ? {
      kms = {
        name           = oci_identity_policy.oke_policy_kms[0].name
        compartment_id = var.tenancy_ocid
        ocid           = oci_identity_policy.oke_policy_kms[0].id
        features       = ["cluster_encryption"]
      }
    } : {}
  )
}
