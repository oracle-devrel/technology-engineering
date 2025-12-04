locals {
  is_npn = var.cni_type == "npn"
  create_pod_subnet = var.create_pod_subnet && local.is_npn && var.create_vcn
  create_cp_subnet = var.create_cp_subnet && var.create_vcn
  create_bastion_subnet = var.create_bastion_subnet && var.create_vcn
  create_fss_subnet = var.create_fss && var.create_vcn
  create_worker_subnet = var.create_worker_subnet && var.create_vcn
  create_external_lb_subnet = var.create_external_lb_subnet && var.create_vcn
  create_internal_lb_subnet = var.create_internal_lb_subnet && var.create_vcn
  all_subnet_private = (var.cp_subnet_private || ! local.create_cp_subnet) && (! local.create_external_lb_subnet) && (var.bastion_subnet_private || ! var.create_bastion_subnet)
  vcn_id = var.create_vcn ? oci_core_vcn.spoke_vcn.0.id : var.vcn_id
  service_gateway_id = var.create_gateways ? oci_core_service_gateway.service_gateway.0.id : null
  nat_gateway_id = var.create_gateways ? oci_core_nat_gateway.nat_gateway.0.id : null
  cp_nat_mode = local.create_cp_subnet && var.cp_subnet_private && var.cp_external_nat
  create_cp_external_traffic_rule = var.allow_external_cp_traffic && (! var.create_cp_subnet || (! var.cp_subnet_private || var.cp_external_nat))

  create_gateways = (var.create_gateways && ! var.create_vcn) || var.create_vcn
  create_internet_gateway = (local.create_gateways && ! var.create_vcn && var.create_internet_gateway) || (var.create_vcn && ! local.all_subnet_private)

  create_drg = var.enable_drg && var.create_drg
  create_drg_attachment = var.enable_drg && var.create_drg_attachment && var.create_vcn
  drg_id = var.create_drg ? try(oci_core_drg.vcn_drg.0.id, null) : var.drg_id


  tcp_protocol = "6"
  icmp_protocol = "1"
  udp_protocol = "17"
  service_cidr_block = lookup(data.oci_core_services.all_oci_services.services[0], "cidr_block")
}
