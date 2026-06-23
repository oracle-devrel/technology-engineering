locals {
  highest_index = length(data.oci_identity_availability_domains.ads.availability_domains) - 1
  last_ad_name  = data.oci_identity_availability_domains.ads.availability_domains[local.highest_index].name
}

resource "oci_core_instance" "standard-instance" {
  for_each             = var.instances
  depends_on           = [oci_objectstorage_object.upload_files]
  availability_domain  = local.last_ad_name
  compartment_id       = local.compartment.id
  display_name         = each.key
  shape                = local.shapes[each.value.arch]
  state                = "RUNNING" # RUNNING or STOPPED

  agent_config {
    are_all_plugins_disabled = false
    is_management_disabled   = false
    is_monitoring_disabled   = false
    plugins_config {
      desired_state = each.value.osmh ? "ENABLED" : "DISABLED"
      name          = "OS Management Hub Agent"
    }
    dynamic "plugins_config" {
      for_each = each.value.arch != "arm" ? [1] : []
      content {
        desired_state = "ENABLED"
        name          = "Management Agent"
      }
    }
  }

  #provisioner "remote-exec" {
  #  inline = [
  #    "echo Hello from Terraform > /tmp/hello.txt"
  #  ]
  #  connection {
  #    type        = "ssh"
  #    user        = "opc"
  #    host        = self.public_ip
  #    private_key = file("~/.ssh/id_ed25519_new")
  #  }
  #}

  shape_config {
    ocpus = 1
    memory_in_gbs = 6
  }

  create_vnic_details {
    subnet_id          = oci_core_subnet.public_subnet.id
    display_name       = "${each.key}-vnic"
    assign_public_ip   = true
    nsg_ids            = each.key == var.command_server_name ? [local.http_nsg.id, local.et_nsg.id] : [local.et_nsg.id]
  }

  source_details {
    source_type = "image"
    #source_id = data.oci_core_images.ol9_arm_latest.images[0].id
    source_id = local.os_images[each.value.os][each.value.arch]
  }

  # Apply the following flag only if you wish to preserve the attached boot volume upon destroying this instance
  # Setting this and destroying the instance will result in a boot volume that should be managed outside of this config.
  # When changing this value, make sure to run 'terraform apply' so that it takes effect before the resource is destroyed.
  #preserve_boot_volume = true

  metadata = {
    ssh_authorized_keys = file("./ssh_authorized_keys")
    #user_data           = base64encode(file("./stage/boot-init.bash"))
    user_data           = base64encode(
                            templatefile("./boot-init.bash.tftpl", {
                              tf_bucket_name = var.bucket_name
                              DOLLAR = "$"
                            })
                          )
  }

  lifecycle {
    ignore_changes = [
      defined_tags, metadata, state, source_details, agent_config
    ]
  }
  defined_tags = {
    "ResourceControl.PatchRing" = each.value.phase
  }

  timeouts {
    create = "60m"
  }
}
