locals {
  is_npn = var.cni_type == "npn"
  create_pod_subnet = var.create_pod_subnet && local.is_npn
  create_cp_subnet = var.create_cp_subnet
  create_worker_subnet = var.create_worker_subnet
  create_service_subnet = var.create_service_subnet
  all_subnet_private = (var.cp_subnet_private || ! local.create_cp_subnet) && (var.service_subnet_private || ! local.create_service_subnet) && (var.bastion_subnet_private || ! var.create_bastion_subnet)
  vcn_id = var.create_vcn ? oci_core_vcn.spoke_vcn.0.id : var.vcn_id
  service_gateway_id = var.create_gateways ? oci_core_service_gateway.service_gateway.0.id : var.service_gateway_id
  nat_gateway_id = var.create_gateways ? oci_core_nat_gateway.nat_gateway.0.id : var.nat_gateway_id
  cp_nat_mode = local.create_cp_subnet && var.cp_subnet_private && var.cp_external_nat
  create_cp_external_traffic_rule = var.allow_external_cp_traffic && (! var.create_cp_subnet || (! var.cp_subnet_private || var.cp_external_nat))
}
