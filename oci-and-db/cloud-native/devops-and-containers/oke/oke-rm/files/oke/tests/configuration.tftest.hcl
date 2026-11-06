mock_provider "oci" {}

mock_provider "oci" {
  alias = "home"
}

override_data {
  target = data.oci_identity_region_subscriptions.home
  values = {
    region_subscriptions = [
      {
        region_name = "eu-frankfurt-1"
      }
    ]
  }
}

override_data {
  target = data.oci_core_subnet.lb_subnet_data[0]
  values = {
    prohibit_public_ip_on_vnic = true
  }
}

override_data {
  target = data.oci_core_subnet.cp_subnet_data
  values = {
    prohibit_public_ip_on_vnic = true
  }
}

override_module {
  target = module.oke
  outputs = {
    cluster_id                      = "ocid1.cluster.oc1.eu-frankfurt-1.test"
    worker_pools                    = {}
    cluster_oidc_discovery_endpoint = null
  }
}

variables {
  tenancy_ocid           = "ocid1.tenancy.oc1..test"
  region                 = "eu-frankfurt-1"
  network_compartment_id = "ocid1.compartment.oc1..network"
  vcn_id                 = "ocid1.vcn.oc1.eu-frankfurt-1.test"
  cp_subnet_id           = "ocid1.subnet.oc1.eu-frankfurt-1.cp"
  cp_nsg_id              = "ocid1.networksecuritygroup.oc1.eu-frankfurt-1.cp"
  worker_subnet_id       = "ocid1.subnet.oc1.eu-frankfurt-1.worker"
  worker_nsg_id          = "ocid1.networksecuritygroup.oc1.eu-frankfurt-1.worker"
  pod_subnet_id          = "ocid1.subnet.oc1.eu-frankfurt-1.pod"
  pod_nsg_id             = "ocid1.networksecuritygroup.oc1.eu-frankfurt-1.pod"
  oke_compartment_id     = "ocid1.compartment.oc1..oke"
  kubernetes_version     = "v1.35.1"
}

run "default_lb_subnet_is_optional" {
  command = plan

  assert {
    condition     = local.lb_subnet_id == "" && length(data.oci_core_subnet.lb_subnet_data) == 0
    error_message = "An omitted LB subnet must leave the default empty without looking up a subnet."
  }
}

run "null_lb_subnet_uses_the_empty_default" {
  command = plan

  variables {
    lb_subnet_id = null
  }

  assert {
    condition     = local.lb_subnet_id == "" && length(data.oci_core_subnet.lb_subnet_data) == 0
    error_message = "A null LB subnet must use the empty default without looking up a subnet."
  }
}

run "blank_lb_subnet_skips_lookup" {
  command = plan

  variables {
    lb_subnet_id = "  "
  }

  assert {
    condition     = local.lb_subnet_id == "" && length(data.oci_core_subnet.lb_subnet_data) == 0
    error_message = "A blank LB subnet must be normalized to empty without looking up a subnet."
  }
}

run "private_lb_subnet_remains_supported" {
  command = plan

  variables {
    lb_subnet_id = "ocid1.subnet.oc1.eu-frankfurt-1.lb"
  }

  assert {
    condition     = local.is_lb_subnet_private && length(data.oci_core_subnet.lb_subnet_data) == 1
    error_message = "A selected private LB subnet must be looked up and classified as private."
  }
}

run "public_lb_subnet_remains_supported" {
  command = plan

  variables {
    lb_subnet_id = "ocid1.subnet.oc1.eu-frankfurt-1.lb"
  }

  override_data {
    target = data.oci_core_subnet.lb_subnet_data[0]
    values = {
      prohibit_public_ip_on_vnic = false
    }
  }

  assert {
    condition     = !local.is_lb_subnet_private && length(data.oci_core_subnet.lb_subnet_data) == 1
    error_message = "A selected public LB subnet must be looked up and classified as public."
  }
}

run "invalid_lb_subnet_is_rejected" {
  command = plan

  variables {
    lb_subnet_id = "not-a-subnet-ocid"
  }

  expect_failures = [var.lb_subnet_id]
}

run "karpenter_policies_require_an_enhanced_cluster" {
  command = plan

  variables {
    cluster_type              = "basic"
    enable_policies           = true
    create_karpenter_policies = true
  }

  expect_failures = [output.cluster_id]
}

run "invalid_cluster_type_is_rejected" {
  command = plan

  variables {
    cluster_type = "unsupported"
  }

  expect_failures = [var.cluster_type]
}

run "autoscaler_policies_require_an_enhanced_cluster" {
  command = plan

  variables {
    cluster_type               = "basic"
    enable_policies            = true
    create_autoscaler_policies = true
  }

  expect_failures = [output.cluster_id]
}

run "vcn_native_requires_pod_network_resources" {
  command = plan

  variables {
    pod_subnet_id = null
    pod_nsg_id    = null
  }

  expect_failures = [output.cluster_id]
}

run "cross_compartment_vcn_native_policies_are_created_before_the_cluster" {
  command = plan

  variables {
    enable_policies = true
  }

  assert {
    condition     = length(oci_identity_policy.oke_policy_cross_compartment_compute) == 1
    error_message = "A compute policy must be created for a cross-compartment VCN-native cluster."
  }

  assert {
    condition     = length(oci_identity_policy.oke_policy_cross_compartment_network) == 1
    error_message = "A network policy must be created for a cross-compartment VCN-native cluster."
  }

  assert {
    condition     = length(local.policy_statements_by_feature.cross_compartment_cni.compute) == 1 && length(local.policy_statements_by_feature.cross_compartment_cni.network) == 2
    error_message = "The cross-compartment policy profile must contain one compute and two network statements."
  }
}

run "same_compartment_autoscaler_policy_is_deduplicated" {
  command = plan

  variables {
    network_compartment_id     = "ocid1.compartment.oc1..oke"
    enable_policies            = true
    create_autoscaler_policies = true
  }

  assert {
    condition     = length(local.autoscaler_compute_statements) == 6
    error_message = "The same-compartment Autoscaler profile must contain six unique statements."
  }

  assert {
    condition     = length(local.autoscaler_network_statements) == 0
    error_message = "The same-compartment Autoscaler profile must not create a duplicate network statement set."
  }

  assert {
    condition     = length(oci_identity_policy.oke_policy_compute) == 1 && length(oci_identity_policy.oke_policy_network) == 0
    error_message = "The same-compartment Autoscaler profile must create one policy resource."
  }
}

run "separate_compartment_autoscaler_policies_keep_both_documented_scopes" {
  command = plan

  variables {
    enable_policies            = true
    create_autoscaler_policies = true
  }

  assert {
    condition     = length(local.autoscaler_compute_statements) == 5 && length(local.autoscaler_network_statements) == 4
    error_message = "The separate-compartment Autoscaler profile must preserve both documented statement sets."
  }
}

run "policy_dry_run_outputs_statements_without_policies" {
  command = plan

  variables {
    enable_policies  = true
    policies_dry_run = true
  }

  assert {
    condition     = length(output.policy_statements) == 3
    error_message = "Dry-run must output the cross-compartment policy statements."
  }

  assert {
    condition     = length(oci_identity_policy.oke_policy_cross_compartment_compute) == 0 && length(oci_identity_policy.oke_policy_cross_compartment_network) == 0
    error_message = "Dry-run must not create cross-compartment IAM policies."
  }
}

run "karpenter_includes_all_required_storage_permissions" {
  command = plan

  variables {
    enable_policies                                       = true
    create_karpenter_policies                             = true
    iam_domain_compartment_id                             = "ocid1.compartment.oc1..identity"
    karpenter_iam_domain_id                               = "ocid1.domain.oc1..test"
    karpenter_dynamic_group_name                          = "oke-test-karpenter"
    create_karpenter_capacity_reservation_policy_optional = true
  }

  assert {
    condition     = strcontains(join("\n", local.karpenter_storage_statements), "manage volume-attachments")
    error_message = "Karpenter must be allowed to manage volume attachments."
  }

  assert {
    condition     = strcontains(local.karpenter_compute_statements[2], "use compute-capacity-reservations")
    error_message = "Karpenter capacity reservation access must use the documented plural resource type."
  }

  assert {
    condition     = strcontains(join("\n", local.karpenter_iam_statements), "inspect compartments in tenancy")
    error_message = "Karpenter compartment inspection must remain tenancy-scoped."
  }
}

run "karpenter_dry_run_does_not_create_identity_resources" {
  command = plan

  variables {
    enable_policies              = true
    policies_dry_run             = true
    create_karpenter_policies    = true
    iam_domain_compartment_id    = "ocid1.compartment.oc1..identity"
    karpenter_iam_domain_id      = "ocid1.domain.oc1..test"
    karpenter_dynamic_group_name = "oke-test-karpenter"
  }

  assert {
    condition     = length(oci_identity_domains_dynamic_resource_group.karpenter_dynamic_group) == 0
    error_message = "Karpenter dry-run must not create a dynamic resource group."
  }

  assert {
    condition     = strcontains(local.karpenter_compute_statements[0], "<karpenter-dynamic-group-ocid>")
    error_message = "Karpenter dry-run must identify the dynamic group OCID placeholder in the CLUSTER_JOIN statement."
  }
}

run "worker_pool_examples_are_disabled_by_default" {
  command = plan

  assert {
    condition     = length(var.worker_pools) == 4 && alltrue([for pool in var.worker_pools : pool.create == false])
    error_message = "All four code-defined example pools must remain disabled by default."
  }

  assert {
    condition     = var.worker_pools["np-ad1"].mode == "node-pool" && var.worker_pools["oke-virtual"].mode == "virtual-node-pool"
    error_message = "The examples must cover managed and virtual nodes only."
  }
}

run "empty_worker_pool_map_is_supported" {
  command = plan

  variables {
    worker_pools = {}
  }

  assert {
    condition     = length(var.worker_pools) == 0
    error_message = "An empty worker pool map must allow a control-plane-only cluster."
  }
}

run "node_pools_are_code_only" {
  command = plan

  assert {
    condition     = yamldecode(file("${path.module}/schema.yaml")).variables.worker_pools.visible == false
    error_message = "Node pools must not be exposed in the Resource Manager form."
  }

  assert {
    condition     = !contains(keys(yamldecode(file("${path.module}/schema.yaml")).variables), "worker_pool_definition") && !contains([for group in yamldecode(file("${path.module}/schema.yaml")).variableGroups : group.title], "Node Pools")
    error_message = "The graphical pool editor and its helper definitions must be removed."
  }
}

run "worker_pool_ad_can_be_omitted" {
  command = plan

  variables {
    worker_pools = { workers = { create = false, size = 1 } }
  }
}

run "worker_pool_positive_ad_is_supported" {
  command = plan

  variables {
    worker_pools = { workers = { create = false, size = 1, placement_ads = [1, 2] } }
  }
}

run "worker_pool_blank_ad_is_rejected" {
  command = plan

  variables {
    worker_pools = { workers = { create = false, size = 1, placement_ads = [""] } }
  }

  expect_failures = [var.worker_pools]
}

run "worker_pool_zero_ad_is_rejected" {
  command = plan

  variables {
    worker_pools = { workers = { create = false, size = 1, placement_ads = [0] } }
  }

  expect_failures = [var.worker_pools]
}

run "custom_worker_pool_attributes_are_preserved" {
  command = plan

  variables {
    worker_pools = {
      app-workers = {
        create             = true
        shape              = "VM.Standard.E5.Flex"
        size               = 2
        ocpus              = 2
        memory             = 16
        kubernetes_version = "v1.34.2"
        node_labels        = { team = "applications" }
        node_metadata      = { custom_metadata = "retained" }
      }
      virtual-workers = {
        create = false
        mode   = "virtual-node-pool"
        shape  = "Pod.Standard.E4.Flex"
        size   = 1
      }
    }
  }

  assert {
    condition     = var.worker_pools["app-workers"].node_metadata.custom_metadata == "retained" && var.worker_pools["app-workers"].kubernetes_version == "v1.34.2"
    error_message = "Pool-specific version overrides and additional module attributes must be preserved."
  }
}

run "worker_pool_creation_must_be_explicit" {
  command = plan

  variables {
    worker_pools = { workers = { shape = "VM.Standard.E5.Flex", size = 1 } }
  }

  expect_failures = [var.worker_pools]
}

run "worker_pool_list_is_rejected" {
  command = plan

  variables {
    worker_pools = [{ create = false, size = 1 }]
  }

  expect_failures = [var.worker_pools]
}

run "invalid_worker_pool_size_is_rejected" {
  command = plan

  variables {
    worker_pools = { workers = { create = true, size = -1 } }
  }

  expect_failures = [var.worker_pools]
}

run "fractional_worker_pool_size_is_rejected" {
  command = plan

  variables {
    worker_pools = { workers = { create = true, size = 1.5 } }
  }

  expect_failures = [var.worker_pools]
}

run "invalid_worker_pool_mode_is_rejected" {
  command = plan

  variables {
    worker_pools = { workers = { create = true, mode = "unsupported" } }
  }

  expect_failures = [var.worker_pools]
}

run "managed_gva_is_supported" {
  command = plan
  variables {
    worker_pools = { workers = { create = false, mode = "node-pool", gva_secondary_vnics = { frontend = { subnet_key = "pods", ip_count = 16 } } } }
  }
}

run "virtual_taints_are_supported" {
  command = plan
  variables {
    worker_pools = { workers = { create = false, mode = "virtual-node-pool", taints = { dedicated = { value = "true", effect = "NoSchedule" } } } }
  }
}

run "managed_taints_are_rejected" {
  command = plan
  variables {
    worker_pools = { workers = { create = false, mode = "node-pool", taints = { dedicated = { value = "true", effect = "NoSchedule" } } } }
  }
  expect_failures = [var.worker_pools]
}

run "virtual_gva_is_rejected" {
  command = plan
  variables {
    worker_pools = { workers = { create = false, mode = "virtual-node-pool", gva_secondary_vnics = { frontend = { subnet_key = "pods", ip_count = 16 } } } }
  }
  expect_failures = [var.worker_pools]
}
