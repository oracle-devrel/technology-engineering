module "containerinstance" {
  source  = "./modules/containerinstance"

  compartment_ocid  = var.compartment_ocid
  private_subnet_ocid = var.private_subnet_ocid
  ci_name = var.ci_name
  ci_restart_policy = var.ci_restart_policy
  ci_state = var.ci_state
  ci_shape = var.ci_shape
  ci_ocpus = var.ci_ocpus
  ci_memory = var.ci_memory
  ci_container_name = var.ci_container_name
  ci_image_url = var.ci_image_url
  ci_registry_secret = var.ci_registry_secret
  ci_count = var.ci_count
  is_public_ip_assigned = var.is_public_ip_assigned
  ci_compartment_id_env = var.ci_compartment_id_env
  ci_genai_endpoint = var.ci_genai_endpoint
  ci_default_model = var.ci_default_model
  tenancy_ocid = var.tenancy_ocid
  user_ocid = var.user_ocid
  fingerprint = var.fingerprint
  private_api_key = var.private_api_key
  region = var.region
}

module "loadbalancer" {
  source  = "./modules/loadbalancer"

  compartment_ocid  = var.compartment_ocid
  public_subnet_ocid = var.public_subnet_ocid
  load_balancer_shape_details_minimum_bandwidth_in_mbps = var.load_balancer_shape_details_minimum_bandwidth_in_mbps
  load_balancer_shape_details_maximum_bandwidth_in_mbps = var.load_balancer_shape_details_maximum_bandwidth_in_mbps
  private_ips = module.containerinstance.private_ips
  lb_name = var.lb_name
  lb_checker_health_port = var.lb_checker_health_port
  lb_checker_url_path = var.lb_checker_url_path
  lb_backend_port = var.lb_backend_port
  lb_listener_port = var.lb_listener_port
}
