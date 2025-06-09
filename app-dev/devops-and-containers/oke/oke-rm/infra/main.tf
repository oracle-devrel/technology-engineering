
module "network" {
  source = "./modules/network"
  network_compartment_id = var.network_compartment_id
  region = var.region
  cni_type = var.cni_type
  # VCN
  create_vcn = var.create_vcn
  vcn_id = var.vcn_id
  vcn_name = var.vcn_name
  vcn_cidr_blocks = var.vcn_cidr_blocks
  vcn_dns_label = var.vcn_dns_label
  # CP SUBNET
  create_cp_subnet = var.create_cp_subnet
  cp_subnet_cidr = var.cp_subnet_cidr
  cp_subnet_dns_label = var.cp_subnet_dns_label
  cp_subnet_name = var.cp_subnet_name
  cp_subnet_private = var.cp_subnet_private
  cp_allowed_source_cidr = var.cp_allowed_source_cidr
  # SERVICE SUBNET
  create_service_subnet = var.create_service_subnet
  service_subnet_cidr = var.service_subnet_cidr
  service_subnet_dns_label = var.service_subnet_dns_label
  service_subnet_name = var.service_subnet_name
  service_subnet_private = var.service_subnet_private
  # WORKER SUBNET
  create_worker_subnet = var.create_worker_subnet
  worker_subnet_cidr = var.worker_subnet_cidr
  worker_subnet_dns_label = var.worker_subnet_dns_label
  worker_subnet_name = var.worker_subnet_name
  # POD SUBNET
  create_pod_subnet = var.create_pod_subnet
  pod_subnet_cidr = var.pod_subnet_cidr
  pod_subnet_dns_label = var.pod_subnet_dns_label
  pod_subnet_name = var.pod_subnet_name
  # BASTION SUBNET
  create_bastion_subnet = var.create_bastion_subnet
  bastion_subnet_cidr = var.bastion_subnet_cidr
  bastion_subnet_dns_label = var.bastion_subnet_dns_label
  bastion_subnet_name = var.bastion_subnet_name
  bastion_subnet_private = var.bastion_subnet_private
  # FSS SUBNET
  create_fss = var.create_fss
  fss_subnet_cidr = var.fss_subnet_cidr
  fss_subnet_dns_label = var.fss_subnet_dns_label
  fss_subnet_name = var.fss_subnet_name
  # GATEWAYS
  create_gateways = var.create_gateways
  nat_gateway_id = var.nat_gateway_id
  service_gateway_id = var.service_gateway_id
  create_internet_gateway = var.create_internet_gateway
  # CONTROL PLANE EXTERNAL CONNECTION
  cp_external_nat = var.cp_external_nat
  allow_external_cp_traffic = var.allow_external_cp_traffic
  cp_egress_cidr = var.cp_egress_cidr
}

module "bastion" {
  source = "./modules/bastion"
  region = var.region
  compartment_id = var.bastion_compartment_id
  vcn_name = var.vcn_name
  bastion_subnet_id = module.network.bastion_subnet_id
  bastion_cidr_block_allow_list = var.bastion_cidr_block_allow_list
  count = local.create_bastion ? 1 : 0
}