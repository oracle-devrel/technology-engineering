#######################################
# Monitoring VM with Management Agent & Grafana
# Centralized monitoring solution for multiple container instances
#######################################

locals {
  # Cloud-init script to install Management Agent and Grafana
  cloud_init_script = templatefile("${path.module}/cloud-init.tpl", {
    mgmt_agent_install_key          = var.mgmt_agent_install_key
    region                          = var.region
    compartment_ocid                = var.compartment_ocid
    grafana_admin_password          = var.grafana_admin_password
    prometheus_port                 = var.prometheus_port
    prometheus_targets              = jsonencode(var.prometheus_targets)
    prometheus_targets_cadvisor     = jsonencode(var.prometheus_targets_cadvisor)
    prometheus_targets_node_exporter = jsonencode(var.prometheus_targets_node_exporter)
    prometheus_targets_nginx_exporter = jsonencode(var.prometheus_targets_nginx_exporter)
    prometheus_targets_redis_exporter = jsonencode(var.prometheus_targets_redis_exporter)
    prometheus_targets_postgres_exporter = jsonencode(var.prometheus_targets_postgres_exporter)
    prometheus_targets_mysql_exporter = jsonencode(var.prometheus_targets_mysql_exporter)
    prometheus_targets_blackbox_exporter = jsonencode(var.prometheus_targets_blackbox_exporter)
    prometheus_targets_app          = jsonencode(var.prometheus_targets_app)
  })
}

#######################################
# Get Latest Oracle Linux Image
#######################################
data "oci_core_images" "oracle_linux" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = var.os_version
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

#######################################
# Compute Instance
#######################################
resource "oci_core_instance" "monitoring_vm" {
  availability_domain = var.availability_domain
  compartment_id      = var.compartment_ocid
  display_name        = "${var.resource_prefix}-monitoring-vm"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  create_vnic_details {
    subnet_id        = var.subnet_ocid
    display_name     = "${var.resource_prefix}-monitoring-vm-vnic"
    assign_public_ip = var.assign_public_ip
    nsg_ids          = var.nsg_ids
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(local.cloud_init_script)
  }

  freeform_tags = var.freeform_tags
  defined_tags  = var.defined_tags
}

#######################################
# Wait for Instance to be Running
#######################################
resource "time_sleep" "wait_for_instance" {
  depends_on = [oci_core_instance.monitoring_vm]

  create_duration = "60s"
}

#######################################
# Data Source to Get Instance Details
#######################################
data "oci_core_instance" "monitoring_vm_data" {
  depends_on  = [time_sleep.wait_for_instance]
  instance_id = oci_core_instance.monitoring_vm.id
}

data "oci_core_vnic_attachments" "monitoring_vm_vnics" {
  depends_on          = [time_sleep.wait_for_instance]
  compartment_id      = var.compartment_ocid
  instance_id         = oci_core_instance.monitoring_vm.id
}

data "oci_core_vnic" "monitoring_vm_vnic" {
  vnic_id = data.oci_core_vnic_attachments.monitoring_vm_vnics.vnic_attachments[0].vnic_id
}
