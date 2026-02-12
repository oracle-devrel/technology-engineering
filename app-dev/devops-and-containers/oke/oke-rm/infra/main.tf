
module "network" {
  source                 = "./modules/network"
  network_compartment_id = var.network_compartment_id
  region                 = var.region
  cni_type               = local.cni
  # VCN
  create_vcn      = var.create_vcn
  vcn_id          = var.vcn_id
  vcn_name        = var.vcn_name
  vcn_cidr_blocks = local.vcn_cidr_blocks
  vcn_dns_label   = var.vcn_dns_label
  # CP SUBNET
  create_cp_subnet       = var.create_cp_subnet
  cp_subnet_cidr         = local.subnets.cidr.cp
  cp_subnet_dns_label    = local.subnets.dns.cp
  cp_subnet_name         = var.cp_subnet_name
  cp_subnet_private      = var.cp_subnet_private
  cp_allowed_source_cidr = var.cp_allowed_source_cidr
  # LB SUBNETS
  create_external_lb_subnet    = var.create_external_lb_subnet
  external_lb_cidr             = local.subnets.cidr.lb_external
  external_lb_subnet_dns_label = local.subnets.dns.lb_external
  external_lb_subnet_name      = var.external_lb_subnet_name
  create_internal_lb_subnet    = var.create_internal_lb_subnet
  internal_lb_cidr             = local.subnets.cidr.lb_internal
  internal_lb_subnet_dns_label = local.subnets.dns.lb_internal
  internal_lb_subnet_name      = var.internal_lb_subnet_name
  # WORKER SUBNET
  create_worker_subnet    = var.create_worker_subnet
  worker_subnet_cidr      = local.subnets.cidr.worker
  worker_subnet_dns_label = local.subnets.dns.worker
  worker_subnet_name      = var.worker_subnet_name
  allow_worker_nat_egress = var.allow_worker_nat_egress
  # POD SUBNET
  create_pod_subnet    = var.create_pod_subnet
  pod_subnet_cidr      = local.subnets.cidr.pod
  pod_subnet_dns_label = local.subnets.dns.pod
  pod_subnet_name      = var.pod_subnet_name
  allow_pod_nat_egress = var.allow_pod_nat_egress
  # BASTION SUBNET
  create_bastion_subnet    = var.create_bastion_subnet
  bastion_subnet_cidr      = local.subnets.cidr.bastion
  bastion_subnet_dns_label = local.subnets.dns.bastion
  bastion_subnet_name      = var.bastion_subnet_name
  bastion_subnet_private   = var.bastion_subnet_private
  # FSS SUBNET
  create_fss           = var.create_fss
  fss_subnet_cidr      = local.subnets.cidr.fss
  fss_subnet_dns_label = local.subnets.dns.fss
  fss_subnet_name      = var.fss_subnet_name
  # DB SUBNET
  create_db_subnet    = var.create_db_subnet
  db_subnet_cidr      = local.subnets.cidr.db
  db_subnet_dns_label = local.subnets.dns.db
  db_subnet_name      = var.db_subnet_name
  db_service_list     = var.db_service_list
  separate_db_nsg     = var.separate_db_nsg
  # GATEWAYS
  create_gateways         = var.create_gateways
  create_internet_gateway = var.create_internet_gateway
  # CONTROL PLANE EXTERNAL CONNECTION
  cp_external_nat           = var.cp_external_nat
  allow_external_cp_traffic = var.allow_external_cp_traffic
  cp_egress_cidr            = var.cp_egress_cidr
  # DRG
  enable_drg            = var.enable_drg
  create_drg            = var.create_drg
  drg_id                = var.drg_id
  drg_name              = var.drg_name
  create_drg_attachment = var.create_drg_attachment
  peer_vcns             = var.peer_vcns
  # Tagging
  tag_value = local.tag_value
}