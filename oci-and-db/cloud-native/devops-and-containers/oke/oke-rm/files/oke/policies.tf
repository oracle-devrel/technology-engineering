locals {
  autoscaler_principal_condition = "ALL {request.principal.type='workload', request.principal.namespace='kube-system', request.principal.service_account='cluster-autoscaler', request.principal.cluster_id='${module.oke.cluster_id}'}"
  karpenter_principal_condition  = "ALL {request.principal.type='workload', request.principal.namespace='${var.karpenter_namespace}', request.principal.service_account='${var.karpenter_service_account}', request.principal.cluster_id='${module.oke.cluster_id}'}"
  cluster_principal_condition    = "ALL {request.principal.type='cluster', request.principal.compartment.id='${var.oke_compartment_id}'}"

  create_cross_compartment_cni_policies = var.enable_policies && var.cni_type == "vcn_native" && var.oke_compartment_id != var.network_compartment_id
  karpenter_dynamic_group_subject       = local.create_karpenter_resources ? oci_identity_domains_dynamic_resource_group.karpenter_dynamic_group[0].ocid : "<karpenter-dynamic-group-ocid>"

  cross_compartment_cni_compute_statements = [
    "Allow any-user to manage instances in compartment id ${var.oke_compartment_id} where ${local.cluster_principal_condition}"
  ]

  cross_compartment_cni_network_statements = [
    "Allow any-user to use private-ips in compartment id ${var.network_compartment_id} where ${local.cluster_principal_condition}",
    "Allow any-user to use network-security-groups in compartment id ${var.network_compartment_id} where ${local.cluster_principal_condition}"
  ]

  cluster_autoscaler_addon_compute_statements = [
    "Allow any-user to manage cluster-node-pools in compartment id ${var.oke_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to manage instance-family in compartment id ${var.oke_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to use subnets in compartment id ${var.oke_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to use vnics in compartment id ${var.oke_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to inspect compartments in compartment id ${var.oke_compartment_id} where ${local.autoscaler_principal_condition}"
  ]

  cluster_autoscaler_addon_network_statements = [
    "Allow any-user to use subnets in compartment id ${var.network_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to read virtual-network-family in compartment id ${var.network_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to use vnics in compartment id ${var.network_compartment_id} where ${local.autoscaler_principal_condition}",
    "Allow any-user to inspect compartments in compartment id ${var.network_compartment_id} where ${local.autoscaler_principal_condition}"
  ]

  # OCI documents one six-statement policy when the node pools and networking share a
  # compartment. When they differ, both compartment-specific sets are required.
  autoscaler_compute_statements = local.create_autoscaler_policies ? (
    var.oke_compartment_id == var.network_compartment_id
    ? distinct(concat(local.cluster_autoscaler_addon_compute_statements, local.cluster_autoscaler_addon_network_statements))
    : local.cluster_autoscaler_addon_compute_statements
  ) : []
  autoscaler_network_statements = local.create_autoscaler_policies && var.oke_compartment_id != var.network_compartment_id ? local.cluster_autoscaler_addon_network_statements : []

  karpenter_compute_statements = [
    local.create_karpenter_policies ? "Allow dynamic-group id ${local.karpenter_dynamic_group_subject} to {CLUSTER_JOIN} in compartment id ${var.oke_compartment_id} where target.cluster.id = '${module.oke.cluster_id}'" : "",
    "Allow any-user to manage instance-family in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}",
    local.create_karpenter_capacity_reservation_policy_optional ? "Allow any-user to use compute-capacity-reservations in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}" : "",
    local.create_karpenter_compute_cluster_policy_optional ? "Allow any-user to use compute-clusters in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}" : "",
    local.create_karpenter_cluster_placement_group_policy_optional ? "Allow any-user to use cluster-placement-groups in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}" : ""
  ]

  karpenter_iam_statements = [
    "Allow any-user to inspect compartments in tenancy where ${local.karpenter_principal_condition}"
  ]

  karpenter_storage_statements = [
    "Allow any-user to manage volumes in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}",
    "Allow any-user to manage volume-attachments in compartment id ${var.oke_compartment_id} where ${local.karpenter_principal_condition}"
  ]

  karpenter_tag_statements = [
    local.create_karpenter_tag_policy_optional ? "Allow any-user to use tag-namespaces in compartment id ${local.tag_compartment_id} where ${local.karpenter_principal_condition}" : ""
  ]

  karpenter_network_statements = [
    "Allow any-user to manage virtual-network-family in compartment id ${var.network_compartment_id} where ${local.karpenter_principal_condition}"
  ]

  oke_kms_statements = var.cluster_kms_key_id != null ? [
    "Allow any-user to use keys in compartment id ${var.kms_compartment_id} where ALL {request.principal.type='cluster', target.key.id='${var.cluster_kms_key_id}'}"
  ] : []

  policy_statements_by_feature = {
    cross_compartment_cni = {
      enabled = local.create_cross_compartment_cni_policies
      compute = local.create_cross_compartment_cni_policies ? local.cross_compartment_cni_compute_statements : []
      network = local.create_cross_compartment_cni_policies ? local.cross_compartment_cni_network_statements : []
    }
    autoscaler = {
      enabled = local.create_autoscaler_policies
      compute = local.autoscaler_compute_statements
      network = local.autoscaler_network_statements
    }
    karpenter = {
      enabled = local.create_karpenter_policies
      compute = local.create_karpenter_policies ? compact(local.karpenter_compute_statements) : []
      network = local.create_karpenter_policies ? local.karpenter_network_statements : []
      storage = local.create_karpenter_policies ? local.karpenter_storage_statements : []
      tag     = local.create_karpenter_policies ? compact(local.karpenter_tag_statements) : []
      iam     = local.create_karpenter_policies ? local.karpenter_iam_statements : []
      dynamic_group = {
        created       = local.create_karpenter_resources
        name          = var.karpenter_dynamic_group_name
        matching_rule = local.karpenter_matching_rule
      }
    }
    cluster_encryption = {
      enabled = var.enable_policies && var.cluster_kms_key_id != null
      kms     = var.enable_policies && var.cluster_kms_key_id != null ? local.oke_kms_statements : []
    }
  }

  compute_statements = distinct(concat(
    local.policy_statements_by_feature.autoscaler.compute,
    local.policy_statements_by_feature.karpenter.compute
  ))
  network_statements = distinct(concat(
    local.policy_statements_by_feature.autoscaler.network,
    local.policy_statements_by_feature.karpenter.network
  ))
  storage_statements = distinct(local.policy_statements_by_feature.karpenter.storage)
  tag_statements     = distinct(local.policy_statements_by_feature.karpenter.tag)
  iam_statements     = distinct(local.policy_statements_by_feature.karpenter.iam)
  kms_statements     = distinct(local.policy_statements_by_feature.cluster_encryption.kms)

  create_cross_compartment_compute_policy = local.create_cross_compartment_cni_policies && !var.policies_dry_run
  create_cross_compartment_network_policy = local.create_cross_compartment_cni_policies && !var.policies_dry_run
  create_compute_policy                   = !var.policies_dry_run && (local.create_autoscaler_policies || local.create_karpenter_policies)
  create_network_policy                   = !var.policies_dry_run && (local.create_karpenter_policies || (local.create_autoscaler_policies && var.oke_compartment_id != var.network_compartment_id))
  create_storage_policy                   = !var.policies_dry_run && local.create_karpenter_policies
  create_tag_policy                       = !var.policies_dry_run && local.create_karpenter_tag_policy_optional
  create_iam_policy                       = !var.policies_dry_run && local.create_karpenter_policies
  create_kms_policy                       = var.enable_policies && var.cluster_kms_key_id != null && !var.policies_dry_run
}

# These policies do not reference the future cluster OCID, so Terraform can create
# them before the OKE module starts provisioning a cross-compartment VCN-native cluster.
resource "oci_identity_policy" "oke_policy_cross_compartment_compute" {
  compartment_id = var.oke_compartment_id
  description    = "Allow OKE clusters in the OKE compartment to manage worker instances"
  name           = "${var.cluster_name}-cross-compartment-compute-policies"
  statements     = local.cross_compartment_cni_compute_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_cross_compartment_compute_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_cross_compartment_network" {
  compartment_id = var.network_compartment_id
  description    = "Allow OKE clusters in the OKE compartment to use VCN-native network resources"
  name           = "${var.cluster_name}-cross-compartment-network-policies"
  statements     = local.cross_compartment_cni_network_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_cross_compartment_network_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_compute" {
  compartment_id = var.oke_compartment_id
  description    = "Compute policies for enabled OKE tools"
  name           = "${var.cluster_name}-compute-policies"
  statements     = local.compute_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_compute_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_network" {
  compartment_id = var.network_compartment_id
  description    = "Network policies for enabled OKE tools"
  name           = "${var.cluster_name}-network-policies"
  statements     = local.network_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_network_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_storage" {
  compartment_id = var.oke_compartment_id
  description    = "Storage policies for enabled OKE tools"
  name           = "${var.cluster_name}-storage-policies"
  statements     = local.storage_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_storage_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_tag" {
  compartment_id = local.tag_compartment_id
  description    = "Tag policies for enabled OKE tools"
  name           = "${var.cluster_name}-tag-policies"
  statements     = local.tag_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_tag_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_iam" {
  compartment_id = var.tenancy_ocid
  description    = "Tenancy-level IAM policies for enabled OKE tools"
  name           = "${var.cluster_name}-iam-policies"
  statements     = local.iam_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_iam_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_kms" {
  compartment_id = var.tenancy_ocid
  description    = "Allow the OKE cluster to use its customer-managed encryption key"
  name           = "${var.cluster_name}-kms-policies"
  statements     = local.oke_kms_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_kms_policy ? 1 : 0
}

# OCI IAM changes are eventually consistent. Wait before the cluster and node pools
# start using policies that must exist before cluster creation.
resource "time_sleep" "await_precluster_policies" {
  count = local.create_kms_policy || local.create_cross_compartment_compute_policy ? 1 : 0

  create_duration = "30s"

  depends_on = [
    oci_identity_policy.oke_policy_kms,
    oci_identity_policy.oke_policy_cross_compartment_compute,
    oci_identity_policy.oke_policy_cross_compartment_network
  ]
}
