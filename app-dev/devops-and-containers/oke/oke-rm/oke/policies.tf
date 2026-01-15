locals {

  cluster_autoscaler_addon_all_statements = [
    "Allow any-user to manage cluster-node-pools in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to manage instance-family in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to use subnets in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to read virtual-network-family in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to use vnics in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}",
    "Allow any-user to inspect compartments in compartment id ${var.oke_compartment_id} where ALL {request.principal.type='workload', request.principal.namespace ='kube-system', request.principal.service_account = 'cluster-autoscaler', request.principal.cluster_id = '${module.oke.cluster_id}'}"
  ]

  cluster_autoscaler_addon_nodepool_statements = [
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

  # Here we do not support yet to have node pools in different compartments than the oke cluster, but it is possible
  node_pool_network_compartment_same = var.oke_compartment_id == var.network_compartment_id

}



resource "oci_identity_policy" "cluster_autoscaler_policy_all" {
  compartment_id = var.oke_compartment_id
  description    = "Policies for the OKE cluster autoscaler using workload identity"
  name           = "${var.cluster_name}-cluster-autoscaler-policies"
  statements     = local.cluster_autoscaler_addon_all_statements
  provider       = oci.home
  count          = local.node_pool_network_compartment_same && local.create_autoscaler_policies ? 1 : 0
}

resource "oci_identity_policy" "cluster_autoscaler_policy_network" {
  compartment_id = var.network_compartment_id
  description    = "Policies for the OKE cluster autoscaler using workload identity"
  name           = "${var.cluster_name}-cluster-autoscaler-policies-network"
  statements     = local.cluster_autoscaler_addon_network_statements
  provider       = oci.home
  count          = !local.node_pool_network_compartment_same && local.create_autoscaler_policies ? 1 : 0
}

resource "oci_identity_policy" "cluster_autoscaler_policy_nodepool" {
  compartment_id = var.oke_compartment_id
  description    = "Policies for the OKE cluster autoscaler using workload identity"
  name           = "${var.cluster_name}-cluster-autoscaler-policies-nodepool"
  statements     = local.cluster_autoscaler_addon_nodepool_statements
  provider       = oci.home
  count          = !local.node_pool_network_compartment_same && local.create_autoscaler_policies ? 1 : 0
}