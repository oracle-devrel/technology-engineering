output "vcn_id" {
  value = local.vcn_id
}

# SUBNETS

output "cp_subnet_id" {
  value = local.create_cp_subnet ? oci_core_subnet.oke_cp_subnet.0.id : null
}

output "pod_subnet_id" {
  value = local.create_pod_subnet ? oci_core_subnet.pods_subnet.0.id : null
}

output "worker_subnet_id" {
  value = local.create_worker_subnet ? oci_core_subnet.worker_subnet.0.id : null
}

output "external_lb_subnet_id" {
  value = local.create_external_lb_subnet ? oci_core_subnet.external_lb_subnet.0.id : null
}

output "internal_lb_subnet_id" {
  value = local.create_internal_lb_subnet ? oci_core_subnet.internal_lb_subnet.0.id : null
}

output "bastion_subnet_id" {
  value = local.create_bastion_subnet ? oci_core_subnet.bastion_subnet[0].id : null
}

output "db_subnet_id" {
  value = local.create_db_subnet ? oci_core_subnet.db_subnet[0].id : null
}

output "db_subnet_created" {
  description = "Whether the database subnet is enabled by the effective configuration."
  value       = local.create_db_subnet
}

output "msg_subnet_id" {
  value = local.create_msg_subnet ? oci_core_subnet.msg_subnet[0].id : null
}

# NSG

output "cp_nsg_id" {
  value = oci_core_network_security_group.cp_nsg.id
}

output "pod_nsg_id" {
  value = local.is_npn ? oci_core_network_security_group.pod_nsg.0.id : null
}

output "worker_nsg_id" {
  value = oci_core_network_security_group.worker_nsg.id
}

output "lb_nsg_id" {
  value = oci_core_network_security_group.oke_lb_nsg.id
}

output "fss_nsg_id" {
  value = oci_core_network_security_group.fss_nsg.id
}

output "database_nsg_ids" {
  value = {
    for service, nsg in oci_core_network_security_group.db : service => nsg.id
  }
}

output "database_client_nsg_ids" {
  value = local.is_npn ? {
    for service, nsg in oci_core_network_security_group.pod_db : service => nsg.id
    } : {
    for service, nsg in oci_core_network_security_group.worker_db : service => nsg.id
  }
}

output "streaming_nsg_id" {
  value = var.create_streaming_nsg ? oci_core_network_security_group.streaming[0].id : null
}

output "network_resource_suffix" {
  value = var.network_resource_suffix
}

output "karpenter_worker_role_tag_value" {
  value = local.karpenter_worker_role_tag_value
}

output "karpenter_pod_role_tag_value" {
  value = local.karpenter_pod_role_tag_value
}

output "nsg_names" {
  value = merge(
    {
      control_plane          = oci_core_network_security_group.cp_nsg.display_name
      worker                 = oci_core_network_security_group.worker_nsg.display_name
      load_balancer_backend  = oci_core_network_security_group.oke_lb_nsg.display_name
      load_balancer_frontend = oci_core_network_security_group.oke_lb_nsg_frontend.display_name
      fss                    = oci_core_network_security_group.fss_nsg.display_name
    },
    local.is_npn ? {
      pod = oci_core_network_security_group.pod_nsg[0].display_name
    } : {},
    local.create_drg_attachment && length(var.peer_vcns) > 0 ? {
      peering = oci_core_network_security_group.peering[0].display_name
    } : {},
    {
      for service, nsg in oci_core_network_security_group.db : "database_${service}" => nsg.display_name
    },
    {
      for service, nsg in oci_core_network_security_group.pod_db : "pod_database_${service}" => nsg.display_name
    },
    {
      for service, nsg in oci_core_network_security_group.worker_db : "worker_database_${service}" => nsg.display_name
    },
    var.create_streaming_nsg ? {
      streaming = oci_core_network_security_group.streaming[0].display_name
    } : {}
  )
}

output "gateway_names" {
  value = merge(
    local.create_gateways ? {
      service = oci_core_service_gateway.service_gateway[0].display_name
    } : {},
    local.create_nat_gateway ? {
      nat = oci_core_nat_gateway.nat_gateway[0].display_name
    } : {},
    local.create_internet_gateway ? {
      internet = oci_core_internet_gateway.internet_gateway[0].display_name
    } : {}
  )
}

output "pod_fss_rule_counts" {
  value = {
    pod_nsg = (
      length(oci_core_network_security_group_security_rule.oke_pod_nsg_fss_tcp_egress) +
      length(oci_core_network_security_group_security_rule.oke_pod_nsg_fss_tcp_ingress) +
      length(oci_core_network_security_group_security_rule.oke_pod_nsg_fss_udp_egress) +
      length(oci_core_network_security_group_security_rule.oke_pod_nsg_fss_udp_ingress)
    )
    fss_nsg = (
      length(oci_core_network_security_group_security_rule.fss_pods_tcp_egress) +
      length(oci_core_network_security_group_security_rule.fss_pods_tcp_ingress) +
      length(oci_core_network_security_group_security_rule.fss_pods_udp_egress) +
      length(oci_core_network_security_group_security_rule.fss_pods_udp_ingress)
    )
  }
}
