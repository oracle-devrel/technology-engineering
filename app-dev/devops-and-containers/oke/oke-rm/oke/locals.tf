locals {
  is_cp_subnet_private = data.oci_core_subnet.cp_subnet_data.prohibit_public_ip_on_vnic
  is_lb_subnet_private = data.oci_core_subnet.lb_subnet_data.prohibit_public_ip_on_vnic
  cni = var.cni_type == "vcn_native" ? "npn" : var.cni_type
  is_flannel = var.cni_type == "flannel"
  enable_cert_manager = var.cluster_type == "enhanced" && var.enable_cert_manager
  enable_metrics_server = var.cluster_type == "enhanced" && var.enable_cert_manager && var.enable_metrics_server
  enable_cluster_autoscaler = var.cluster_type == "enhanced" && var.enable_cluster_autoscaler
  create_autoscaler_policies = var.cluster_type == "enhanced"&& var.enable_cluster_autoscaler && var.create_autoscaler_policies
}