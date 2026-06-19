#######################################
# OCI Container Instance Monitoring
# Main Terraform Configuration
#######################################

#######################################
# Automatic IP Detection for NSG
#######################################
data "http" "my_ip" {
  url = "https://ifconfig.me/ip"
}

locals {
  # Container environment variables (already a map)
  container_env_map = var.container_env_vars

  # NSG OCIDs (already a list)
  nsg_list = var.nsg_ocids

  # Detected public IP for NSG rules
  my_ip_cidr = "${chomp(data.http.my_ip.response_body)}/32"

  # Common tags (CreatedDate removed to prevent constant updates)
  common_tags = merge(
    var.freeform_tags,
    {
      Project   = "OCI-Container-Monitoring"
      Terraform = "true"
    }
  )

  # Use module output directly - circular dependency is broken by removing from depends_on
  application_log_ocid = var.enable_logging && var.enable_log_forwarder_sidecar ? module.logging[0].application_log_id : ""
}

#######################################
# IAM Policies and Dynamic Groups
#######################################
module "iam" {
  source = "./modules/iam"

  tenancy_ocid              = var.tenancy_ocid
  compartment_ocid          = var.compartment_ocid
  resource_prefix           = var.container_instance_name
  create_dynamic_groups     = true
  create_policies           = true
  enable_management_agent   = var.enable_management_agent
  enable_alarms             = var.enable_alarms

  freeform_tags = local.common_tags
}

#######################################
# Network Security Group
# Automatically allows access from the user's detected IP
#######################################
module "nsg" {
  source = "./modules/nsg"

  compartment_ocid     = var.compartment_ocid
  vcn_ocid             = var.vcn_ocid
  resource_prefix      = var.container_instance_name
  allowed_cidr         = local.my_ip_cidr
  create_container_nsg = true
  create_vm_nsg        = false

  freeform_tags = local.common_tags
  defined_tags  = var.defined_tags

  depends_on = [module.iam]
}

#######################################
# Container Instance Deployment
#######################################
module "container_instance" {
  source = "./modules/container-instance"

  tenancy_ocid            = var.tenancy_ocid
  compartment_ocid        = var.compartment_ocid
  container_instance_name = var.container_instance_name
  container_image         = var.container_image
  container_shape         = var.container_shape
  container_ocpus         = var.container_ocpus
  container_memory_gb     = var.container_memory_gb
  container_count         = var.container_count
  container_port          = var.container_port
  container_env_vars      = local.container_env_map
  availability_domain     = var.availability_domain
  subnet_ocid             = var.subnet_ocid
  assign_public_ip        = var.assign_public_ip
  nsg_ocids               = concat([module.nsg.container_nsg_id], local.nsg_list)
  ocir_username           = var.ocir_username
  ocir_auth_token         = var.ocir_auth_token
  ocir_endpoint           = "${var.region}.ocir.io"

  # Management Agent configuration (Legacy)
  enable_management_agent    = var.enable_management_agent
  mgmt_agent_install_key     = (var.enable_management_agent || var.enable_management_agent_sidecar) ? module.management_agent[0].install_key : ""
  region                     = var.region
  prometheus_scrape_interval = var.prometheus_scrape_interval
  prometheus_scrape_timeout  = var.prometheus_scrape_timeout
  prometheus_metrics_port    = var.prometheus_metrics_port
  prometheus_metrics_path    = var.prometheus_metrics_path
  metrics_namespace          = var.metrics_namespace

  # Sidecar Architecture Configuration (New)
  enable_shared_volumes             = var.enable_shared_volumes
  enable_management_agent_sidecar   = var.enable_management_agent_sidecar
  enable_prometheus_sidecar         = var.enable_prometheus_sidecar
  mgmt_agent_sidecar_image          = var.mgmt_agent_sidecar_image
  prometheus_sidecar_image          = var.prometheus_sidecar_image
  mgmt_agent_sidecar_memory_gb      = var.mgmt_agent_sidecar_memory_gb
  mgmt_agent_sidecar_ocpus          = var.mgmt_agent_sidecar_ocpus
  prometheus_sidecar_memory_gb      = var.prometheus_sidecar_memory_gb
  prometheus_sidecar_ocpus          = var.prometheus_sidecar_ocpus
  enable_log_forwarder_sidecar      = var.enable_log_forwarder_sidecar
  log_forwarder_sidecar_image       = var.log_forwarder_sidecar_image
  log_forwarder_sidecar_memory_gb   = var.log_forwarder_sidecar_memory_gb
  log_forwarder_sidecar_ocpus       = var.log_forwarder_sidecar_ocpus
  # Use local variable to avoid circular dependency
  log_ocid                          = local.application_log_ocid

  # Grafana Sidecar Configuration (New)
  enable_grafana_sidecar            = var.enable_grafana_sidecar
  grafana_sidecar_image             = var.grafana_sidecar_image
  grafana_sidecar_memory_gb         = var.grafana_sidecar_memory_gb
  grafana_sidecar_ocpus             = var.grafana_sidecar_ocpus
  grafana_admin_user                = var.grafana_admin_user
  grafana_admin_password            = var.grafana_admin_password

  # Prometheus Exporters Configuration
  enable_prometheus_exporters = var.enable_prometheus_exporters
  enable_nginx_exporter       = var.enable_nginx_exporter
  enable_redis_exporter       = var.enable_redis_exporter
  enable_postgres_exporter    = var.enable_postgres_exporter
  enable_mysql_exporter       = var.enable_mysql_exporter
  enable_blackbox_exporter    = var.enable_blackbox_exporter

  freeform_tags = local.common_tags
  defined_tags  = var.defined_tags

  # Note: logging dependency removed to avoid circular dependency during destroy
  depends_on = [module.iam, module.nsg, module.management_agent]
}

#######################################
# Logging Configuration
#######################################
module "logging" {
  count = var.enable_logging ? 1 : 0

  source = "./modules/logging"

  compartment_ocid        = var.compartment_ocid
  log_group_name          = var.log_group_name
  enable_logging          = var.enable_logging
  enable_audit_logs       = var.enable_audit_logs
  enable_management_agent = var.enable_management_agent
  log_retention_days      = var.log_retention_days

  freeform_tags = local.common_tags
  defined_tags  = var.defined_tags
}

#######################################
# Management Agent Install Key
# Note: For sidecar pattern, we only need the install key
# The agent configuration is done within the container instance
#######################################
module "management_agent" {
  count = (var.enable_management_agent || var.enable_management_agent_sidecar) ? 1 : 0

  source = "./modules/management-agent"

  compartment_ocid           = var.compartment_ocid
  region                     = var.region
  install_key_name           = var.mgmt_agent_install_key_name
  prometheus_scrape_interval = var.prometheus_scrape_interval
  prometheus_metrics_port    = var.prometheus_metrics_port
  prometheus_metrics_path    = var.prometheus_metrics_path
  prometheus_targets         = []  # Empty for sidecar - scrapes localhost
  prometheus_job_name        = "container-${var.container_instance_name}"
  metrics_namespace          = var.metrics_namespace
  container_instance_id      = ""  # Not needed for sidecar pattern
  container_private_ip       = ""  # Not needed for sidecar pattern
  output_directory           = "${path.root}/output"

  additional_prometheus_labels = {
    container_name = var.container_instance_name
    environment    = lookup(var.freeform_tags, "Environment", "Development")
  }

  freeform_tags = local.common_tags

  depends_on = [module.iam]
}

#######################################
# Monitoring Alarms (Optional)
#######################################
resource "oci_monitoring_alarm" "cpu_alarm" {
  count              = var.enable_alarms ? 1 : 0
  compartment_id     = var.compartment_ocid
  display_name       = "${var.container_instance_name}-cpu-alarm"
  is_enabled         = true
  metric_compartment_id = var.compartment_ocid
  namespace          = "oci_computecontainerinstance"

  query = <<-EOT
    CpuUtilization[1m]{resourceId = "${module.container_instance.container_instance_id}"}.mean() > ${var.cpu_alarm_threshold}
  EOT

  severity = "CRITICAL"

  destinations = var.notification_topic_ocid != "" ? [var.notification_topic_ocid] : []

  body = "CPU utilization for ${var.container_instance_name} exceeded ${var.cpu_alarm_threshold}%"

  repeat_notification_duration = "PT2H"

  freeform_tags = local.common_tags
}

resource "oci_monitoring_alarm" "memory_alarm" {
  count              = var.enable_alarms ? 1 : 0
  compartment_id     = var.compartment_ocid
  display_name       = "${var.container_instance_name}-memory-alarm"
  is_enabled         = true
  metric_compartment_id = var.compartment_ocid
  namespace          = "oci_computecontainerinstance"

  query = <<-EOT
    MemoryUtilization[1m]{resourceId = "${module.container_instance.container_instance_id}"}.mean() > ${var.memory_alarm_threshold}
  EOT

  severity = "CRITICAL"

  destinations = var.notification_topic_ocid != "" ? [var.notification_topic_ocid] : []

  body = "Memory utilization for ${var.container_instance_name} exceeded ${var.memory_alarm_threshold}%"

  repeat_notification_duration = "PT2H"

  freeform_tags = local.common_tags
}
