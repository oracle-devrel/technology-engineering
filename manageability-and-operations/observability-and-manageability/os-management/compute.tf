
resource oci_core_instance golden_instance {
  count = length(local.golden_instances)
  availability_domain = local.availability_domain_name
  compartment_id = var.compartment_ocid
  shape = var.shape
  state = local.golden_instances[count.index].state

  lifecycle {
    ignore_changes = [
      source_details, # ignore if newer image is available after creation
      #state
    ]
  }

  agent_config {
    are_all_plugins_disabled = false
    is_management_disabled = false
    is_monitoring_disabled = false
    plugins_config {
      name = "Vulnerability Scanning"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Oracle Java Management Service"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "OS Management Service Agent"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Compute Instance Run Command"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Compute Instance Monitoring"
      desired_state = "ENABLED"
    }
  }
  shape_config {
    ocpus = 1
    memory_in_gbs = 16
  }
  source_details {
    source_id = local.os_images[local.golden_instances[count.index].os]
    source_type = "image"
  }
  defined_tags = var.defined_tags

  # Optional
  display_name = "${local.golden_instances[count.index].name}"
  create_vnic_details {
    assign_public_ip = !oci_core_subnet.vcn-subnet[local.golden_instances[count.index].subnet].prohibit_internet_ingress
    subnet_id = oci_core_subnet.vcn-subnet[local.golden_instances[count.index].subnet].id
  }
  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  } 
  preserve_boot_volume = false
}

resource oci_core_instance managed_instances {
  count = length(local.servers)
  availability_domain = local.availability_domain_name
  compartment_id = var.compartment_ocid
  shape = var.shape
  state = local.servers[count.index].state

  lifecycle {
    ignore_changes = [
      source_details, # ignore if newer image is available after creation
      #state
    ]
  }

  agent_config {
    are_all_plugins_disabled = false
    is_management_disabled = false
    is_monitoring_disabled = false
    plugins_config {
      name = "Vulnerability Scanning"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Oracle Java Management Service"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "OS Management Service Agent"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Compute Instance Run Command"
      desired_state = "ENABLED"
    }
    plugins_config {
      name = "Compute Instance Monitoring"
      desired_state = "ENABLED"
    }
  }
  shape_config {
    ocpus = 1
    memory_in_gbs = 16
  }
  source_details {
    source_id = local.os_images[local.servers[count.index].os]
    source_type = "image"
  }
  defined_tags = var.defined_tags

  # Optional
  display_name = "${local.servers[count.index].name}"
  create_vnic_details {
    assign_public_ip = !oci_core_subnet.vcn-subnet[local.servers[count.index].subnet].prohibit_internet_ingress
    subnet_id = oci_core_subnet.vcn-subnet[local.servers[count.index].subnet].id
  }
  metadata = {
    ssh_authorized_keys = var.ssh_public_key
  } 
  preserve_boot_volume = false
}
