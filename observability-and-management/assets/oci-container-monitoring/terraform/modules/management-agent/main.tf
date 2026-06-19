#######################################
# OCI Management Agent Module
# Creates Management Agent install key and configuration
# for Prometheus metrics collection
#######################################

#######################################
# Management Agent Install Key
#######################################
resource "oci_management_agent_management_agent_install_key" "main" {
  compartment_id = var.compartment_ocid
  display_name   = var.install_key_name

  # Install key validity in days
  time_expires = timeadd(timestamp(), "${var.install_key_validity_days * 24}h")

  # Allowed key attributes
  allowed_key_install_count = var.allowed_install_count
  is_unlimited              = var.is_unlimited_install

  lifecycle {
    ignore_changes = [time_expires]
  }
}

#######################################
# Generate Management Agent Configuration
#######################################
locals {
  # Agent configuration for Prometheus scraping
  agent_config = {
    install_key = oci_management_agent_management_agent_install_key.main.key
    install_key_id = oci_management_agent_management_agent_install_key.main.id
    compartment_id = var.compartment_ocid
    prometheus_config = {
      scrape_interval = "${var.prometheus_scrape_interval}s"
      scrape_timeout  = "${var.prometheus_scrape_timeout}s"
      metrics_path    = var.prometheus_metrics_path
      targets         = var.prometheus_targets
    }
    metrics_namespace = var.metrics_namespace
  }

  # Install script content
  install_script = templatefile("${path.module}/templates/install-agent.sh.tpl", {
    install_key        = oci_management_agent_management_agent_install_key.main.key
    region             = var.region
    compartment_ocid   = var.compartment_ocid
    agent_version      = var.agent_version != "" ? var.agent_version : "latest"
    install_dir        = var.install_directory
  })

  # Prometheus configuration file
  prometheus_config = templatefile("${path.module}/templates/prometheus-config.yml.tpl", {
    scrape_interval   = var.prometheus_scrape_interval
    scrape_timeout    = var.prometheus_scrape_timeout
    metrics_path      = var.prometheus_metrics_path
    targets           = var.prometheus_targets
    metrics_namespace = var.metrics_namespace
    job_name          = var.prometheus_job_name
    additional_labels = var.additional_prometheus_labels
  })

  # Service discovery configuration
  service_discovery_config = templatefile("${path.module}/templates/service-discovery.json.tpl", {
    container_instance_id = var.container_instance_id
    container_ip          = var.container_private_ip
    metrics_port          = var.prometheus_metrics_port
    compartment_ocid      = var.compartment_ocid
  })
}

#######################################
# Store configurations in Object Storage (Optional)
#######################################
resource "oci_objectstorage_object" "agent_install_script" {
  count      = var.store_configs_in_object_storage ? 1 : 0
  namespace  = var.object_storage_namespace
  bucket     = var.object_storage_bucket
  object     = "management-agent/install-agent.sh"
  content    = local.install_script
  content_type = "text/plain"

  metadata = {
    "install-key-id" = oci_management_agent_management_agent_install_key.main.id
  }
}

resource "oci_objectstorage_object" "prometheus_config" {
  count      = var.store_configs_in_object_storage ? 1 : 0
  namespace  = var.object_storage_namespace
  bucket     = var.object_storage_bucket
  object     = "management-agent/prometheus-config.yml"
  content    = local.prometheus_config
  content_type = "application/x-yaml"
}

resource "oci_objectstorage_object" "service_discovery_config" {
  count      = var.store_configs_in_object_storage ? 1 : 0
  namespace  = var.object_storage_namespace
  bucket     = var.object_storage_bucket
  object     = "management-agent/service-discovery.json"
  content    = local.service_discovery_config
  content_type = "application/json"
}

#######################################
# Write configurations to local files
#######################################
resource "local_file" "agent_install_script" {
  content  = local.install_script
  filename = "${var.output_directory}/install-agent.sh"
  file_permission = "0755"
}

resource "local_file" "prometheus_config" {
  content  = local.prometheus_config
  filename = "${var.output_directory}/prometheus-config.yml"
  file_permission = "0644"
}

resource "local_file" "service_discovery_config" {
  content  = local.service_discovery_config
  filename = "${var.output_directory}/service-discovery.json"
  file_permission = "0644"
}

resource "local_file" "agent_config_json" {
  content  = jsonencode(local.agent_config)
  filename = "${var.output_directory}/agent-config.json"
  file_permission = "0644"
}
