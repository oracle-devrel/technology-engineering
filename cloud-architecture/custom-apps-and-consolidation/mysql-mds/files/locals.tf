# Copyright (c) 2023, Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v1.0 as shown at https://oss.oracle.com/licenses/upl.
# Purpose: terraform configuration file to declare local variables.
# @author: Vijay Kokatnur

locals {
  all_protocols = "all"

  anywhere = "0.0.0.0/0"

  autonomous_template = "${path.module}/cloudinit/autonomous.template.yaml"

  image_id = var.image_id == "Autonomous" ? data.oci_core_images.autonomous_images.images.0.id : var.image_id

  ssh_port = 22

  tcp_protocol = 6

  ADs = [
    // Iterate through data.oci_identity_availability_domains.ad and create a list containing AD names
    for i in data.oci_identity_availability_domains.ad.availability_domains : i.name
  ]

  backup_policies = {
    // Iterate through data.oci_core_volume_backup_policies.default_backup_policies and create a map containing name & ocid
    // This is used to specify a backup policy id by name
    for i in data.oci_core_volume_backup_policies.default_backup_policies.volume_backup_policies : i.display_name => i.id
  }

  ssh_private_key =  file(var.ssh_private_key_path)
}
