packer {
  required_plugins {
    oracle = {
      version = "~> 1"
      source  = "github.com/hashicorp/oracle"
    }
  }
}


# Packer configuration for building OKE custom image

source "oracle-oci" "oke_builder" {
  availability_domain = var.availability_domain
  base_image_ocid     = var.base_image_ocid
  compartment_ocid    = var.compartment_ocid
  image_name          = "${var.image_prefix}${formatdate("YYYY-MM-DD-hh-mm-ss", timestamp())}"
  shape               = var.shape

  shape_config {
    ocpus         = var.ocpus
    memory_in_gbs = var.memory_in_gbs
  }
  subnet_ocid  = var.subnet_ocid
  ssh_username = var.ssh_username
  region       = var.region

  skip_create_image = var.skip_create_image
}

build {
  sources = ["source.oracle-oci.oke_builder"]

  # Update the base image
  provisioner "shell" {
    inline = [
      "sudo yum-config-manager --enable ol8_developer",
      "sudo dnf update -y",
      "sudo dnf upgrade -y"
    ]
  }

  # Install oci-fss-utils, required for in-transit encryption while using OCI FSS
  provisioner "shell" {
    inline = [
      "sudo dnf install -y oci-fss-utils"
    ]
  }

  # Install OCI CLI, as it is needed to update the Oracle Cloud Agent and for enabling Ultra High Performance block volume attachments
  provisioner "shell" {
    inline = [
      "sudo dnf install -y python36-oci-cli"
    ]
  }

  # Stop the dnf-makecache timer so that node resources are not periodically wasted
  provisioner "shell" {
    inline = [
      "sudo systemctl stop dnf-makecache.timer",
      "sudo systemctl disable dnf-makecache.timer"
    ]
  }

  # Enable cgroups v2
  provisioner "shell" {
    inline = [
      "sudo grubby --update-kernel=ALL --args=\"systemd.unified_cgroup_hierarchy=1\"",
      "sudo reboot"
    ]
    expect_disconnect = true
    pause_before      = "10s"
  }
}
