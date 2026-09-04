locals {
  is_cp_subnet_private                                     = data.oci_core_subnet.cp_subnet_data.prohibit_public_ip_on_vnic
  is_lb_subnet_private                                     = data.oci_core_subnet.lb_subnet_data.prohibit_public_ip_on_vnic
  cni                                                      = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  is_flannel                                               = var.cni_type == "flannel"
  enable_cert_manager                                      = var.cluster_type == "enhanced" && var.enable_cert_manager
  enable_metrics_server                                    = var.cluster_type == "enhanced" && var.enable_cert_manager && var.enable_metrics_server
  create_karpenter_policies                                = var.cluster_type == "enhanced" && var.enable_policies && var.create_karpenter_policies
  create_karpenter_cluster_placement_group_policy_optional = local.create_karpenter_policies && var.create_karpenter_cluster_placement_group_policy_optional
  create_karpenter_tag_policy_optional                     = local.create_karpenter_policies && var.create_karpenter_tag_policy_optional
  tag_compartment_id                                       = local.create_karpenter_tag_policy_optional ? var.tag_compartment_id : ""
  create_karpenter_capacity_reservation_policy_optional    = local.create_karpenter_policies && var.create_karpenter_capacity_reservation_policy_optional
  create_karpenter_compute_cluster_policy_optional         = local.create_karpenter_policies && var.create_karpenter_compute_cluster_policy_optional
  create_autoscaler_policies                               = var.cluster_type == "enhanced" && var.enable_policies && var.create_autoscaler_policies
  tag_value                                                = var.tag_value == null ? { "freeformTags" = {}, "definedTags" = {} } : var.tag_value
}

# OIDC
locals {
  oidc_discovery_enabled      = var.cluster_type == "enhanced" && var.enable_oidc_discovery
  oidc_authentication_enabled = var.cluster_type == "enhanced" && var.enable_oidc_authentication
  oidc_token_authentication_config = {
    client_id       = var.oidc_client_id
    issuer_url      = var.oidc_issuer
    username_claim  = var.oidc_username_claim
    username_prefix = var.oidc_username_prefix
    groups_claim    = var.oidc_groups_claim
    groups_prefix   = var.oidc_groups_prefix
  }

}