   
resource "oci_core_instance" "starter_compute" {

  availability_domain = local.availability_domain_name
  compartment_id      = local.lz_app_cmp_ocid
  display_name        = "${var.prefix}-compute"
  shape               = local.shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_shape_config_memory_in_gbs
    # baseline_ocpu_utilization = "BASELINE_1_8"
  }

  create_vnic_details {
    subnet_id                 = data.oci_core_subnet.starter_web_subnet.id
    assign_public_ip          = true
    display_name              = "Primaryvnic"
    assign_private_dns_record = true
    hostname_label            = "${var.prefix}-compute"
  }

  agent_config {
    # plugins_config {
    #   desired_state =  "ENABLED"
    #   name = "Oracle Java Management Service"
    # }
    plugins_config {
      desired_state =  "ENABLED"
      name = "Management Agent"
    }
  }

  metadata = {
    ssh_authorized_keys = local.ssh_public_key
  }

  source_details {
    source_type = "image"
    # boot_volume_size_in_gbs = "50" 
    source_id   = data.oci_core_images.oraclelinux.images.0.id
  }

  connection {
    agent       = false
    host        = oci_core_instance.starter_compute.public_ip
    user        = "opc"
    private_key = local.ssh_private_key
  }

  lifecycle {
    ignore_changes = [
      source_details[0].source_id,
      shape
    ]
  }
  
  freeform_tags = local.freeform_tags
}

data "oci_core_instance" "starter_compute" {
    instance_id = oci_core_instance.starter_compute.id
}   

locals {
  compute_ocid = data.oci_core_instance.starter_compute.id
  compute_public_ip = data.oci_core_instance.starter_compute.public_ip
  local_compute_ip = data.oci_core_instance.starter_compute.private_ip
}

output "compute_ip" {
  value = local.local_compute_ip
}