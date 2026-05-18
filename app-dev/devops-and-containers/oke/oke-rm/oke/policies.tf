locals {

  cluster_autoscaler_addon_compute_statements = [
    "Allow any-user to manage cluster-node-pools in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to manage instance-family in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to use subnets in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to use vnics in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to inspect compartments in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  cluster_autoscaler_addon_network_statements = [
    "Allow any-user to use subnets in compartment id ${var.network_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to read virtual-network-family in compartment id ${var.network_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to use vnics in compartment id ${var.network_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to inspect compartments in compartment id ${var.network_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  #"Allow any-user to manage volume-attachments in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  karpenter_compute_statements = [
    var.create_karpenter_policies ? "Allow dynamic-group id ${oci_identity_domains_dynamic_resource_group.karpenter_dynamic_group.0.ocid} to {CLUSTER_JOIN} in compartment id ${var.oke_compartment_id} where { target.cluster.id = '${module.oke.cluster_id}' }" : "",
    "Allow any-user to manage instance-family in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    local.create_karpenter_capacity_reservation_policy_optional ? "Allow any-user to use compute-capacity-reservation in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}" : "",
    local.create_karpenter_compute_cluster_policy_optional ? "Allow any-user to use compute-clusters in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}" : "",
    local.create_karpenter_cluster_placement_group_policy_optional ? "Allow any-user to use cluster-placement-groups in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}" : ""
  ]

  karpenter_iam_statements = [
    "Allow any-user to inspect compartments in tenancy where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  karpenter_storage_statements = [
    "Allow any-user to manage volumes in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  karpenter_tag_statements = [
    local.create_karpenter_tag_policy_optional ? "Allow any-user to use tag-namespaces in compartment id ${local.tag_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}" : ""
  ]

  karpenter_network_statements = [
    "Allow any-user to manage virtual-network-family in compartment id ${var.network_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='karpenter', request.principal.service_account = 'karpenter', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  oke_kms_statements = [
    var.cluster_kms_key_id != null ? "Allow any-user to use keys in compartment id ${var.kms_compartment_id} where ALL {request.principal.type = 'cluster', target.key.id = '${var.cluster_kms_key_id}', request.principal.cluster_id = '${module.oke.cluster_id}'}" : ""
  ]


  compute_statements = distinct(
    compact(
      concat(
        local.create_autoscaler_policies ? local.cluster_autoscaler_addon_compute_statements : [],
        local.create_karpenter_policies ? local.karpenter_compute_statements : []
      )
    )
  )

  network_statements = distinct(
    compact(
      concat(
        local.create_autoscaler_policies ? local.cluster_autoscaler_addon_network_statements : [],
        local.create_karpenter_policies ? local.karpenter_network_statements : []
      )
    )
  )

  storage_statements = distinct(
    compact(
      concat(
        local.create_karpenter_policies ? local.karpenter_storage_statements : [],
        []
      )
    )
  )

  tag_statements = distinct(
    compact(
      concat(
        local.create_karpenter_policies ? local.karpenter_tag_statements : [],
        []
      )
    )
  )

  kms_statements = distinct(
    compact(
      concat(
        var.cluster_kms_key_id != null ? local.oke_kms_statements : [],
        []
      )
    )
  )

  iam_statements = distinct(
    compact(
      concat(
        local.create_karpenter_policies ? local.karpenter_iam_statements : [],
        []
      )
    )
  )

  create_compute_policy = !var.policies_dry_run && (local.create_autoscaler_policies || local.create_karpenter_policies)
  create_network_policy = !var.policies_dry_run && (local.create_autoscaler_policies || local.create_karpenter_policies)
  create_storage_policy = !var.policies_dry_run && local.create_karpenter_policies
  create_tag_policy     = !var.policies_dry_run && local.create_karpenter_tag_policy_optional
  create_iam_policy     = !var.policies_dry_run && local.create_karpenter_policies
  create_kms_policy     = !var.policies_dry_run && var.cluster_kms_key_id != null
}

resource "oci_identity_policy" "oke_policy_compute" {
  compartment_id = var.oke_compartment_id
  description    = "Policies to allow OKE and tools to manage compute resources"
  name           = "${var.cluster_name}-compute-policies"
  statements     = local.compute_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_compute_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_network" {
  compartment_id = var.network_compartment_id
  description    = "Policies to allow OKE and tools to manage network resources"
  name           = "${var.cluster_name}-network-policies"
  statements     = local.network_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_network_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_storage" {
  compartment_id = var.oke_compartment_id
  description    = "Policies to allow OKE and tools to manage storage resources"
  name           = "${var.cluster_name}-storage-policies"
  statements     = local.storage_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_storage_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_tag" {
  compartment_id = local.tag_compartment_id
  description    = "Policies to allow OKE and tools to use tags"
  name           = "${var.cluster_name}-tag-policies"
  statements     = local.tag_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_tag_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_iam" {
  compartment_id = var.tenancy_ocid
  description    = "Policies to allow OKE and tools to use iam resources"
  name           = "${var.cluster_name}-iam-policies"
  statements     = local.iam_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_iam_policy ? 1 : 0
}

resource "oci_identity_policy" "oke_policy_kms" {
  compartment_id = var.tenancy_ocid
  description    = "Policies to allow OKE and tools to use kms resources"
  name           = "${var.cluster_name}-kms-policies"
  statements     = local.kms_statements
  freeform_tags  = local.tag_value.freeformTags
  defined_tags   = local.tag_value.definedTags
  provider       = oci.home
  count          = local.create_kms_policy ? 1 : 0
}
