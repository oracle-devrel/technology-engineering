# Copyright (c) 2023 Oracle and/or its affiliates.
#
# The Universal Permissive License (UPL), Version 1.0
#
# Subject to the condition set forth below, permission is hereby granted to any
# person obtaining a copy of this software, associated documentation and/or data
# (collectively the "Software"), free of charge and under any and all copyright
# rights in the Software, and any and all patent rights owned or freely
# licensable by each licensor hereunder covering either (i) the unmodified
# Software as contributed to or provided by such licensor, or (ii) the Larger
# Works (as defined below), to deal in both
#
# (a) the Software, and
# (b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
# one is included with the Software (each a "Larger Work" to which the Software
# is contributed by such licensors),
# without restriction, including without limitation the rights to copy, create
# derivative works of, display, perform, and distribute the Software and make,
# use, sell, offer for sale, import, export, have made, and have sold the
# Software and the Larger Work(s), and to sublicense the foregoing rights on
# either these or other terms.
#
# This license is subject to the following condition:
# The above copyright notice and either this complete permission notice or at
# a minimum a reference to the UPL must be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

resource "tls_private_key" "rsa-key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource oci_core_instance jenkins_instance {
  agent_config {
    are_all_plugins_disabled = false
    is_management_disabled   = false
    is_monitoring_disabled   = false
    plugins_config {
      desired_state = "DISABLED"
      name          = "Vulnerability Scanning"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Oracle Java Management Service"
    }
    plugins_config {
      desired_state = "ENABLED"
      name          = "OS Management Service Agent"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Compute RDMA GPU Monitoring"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Compute Instance Run Command"
    }
    plugins_config {
      desired_state = "ENABLED"
      name          = "Compute Instance Monitoring"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Compute HPC RDMA Auto-Configuration"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Compute HPC RDMA Authentication"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Block Volume Management"
    }
    plugins_config {
      desired_state = "DISABLED"
      name          = "Bastion"
    }
  }
  availability_domain = var.instance_ad
  compartment_id = var.compartment_ocid
  create_vnic_details {
    assign_public_ip = true
    subnet_id = var.instance_subnet
  }
  display_name = var.instance_name
  instance_options {
    are_legacy_imds_endpoints_disabled = true
  }
  metadata = {
    "ssh_authorized_keys" = trimspace(tls_private_key.rsa-key.public_key_openssh)
  }
  shape = "VM.Standard.A1.Flex"
  shape_config {
    memory_in_gbs             = var.instance_memory
    ocpus                     = var.instance_ocpu
  }
  source_details {
    boot_volume_size_in_gbs = var.custom_boot_volume_size
    boot_volume_vpus_per_gb = "10"
    source_id   = var.image_ocid
    source_type = "image"
  }
}

resource "local_sensitive_file" "private_ssh" {
  filename = "${path.root}/jenkins-playbook/private.key"
  content = tls_private_key.rsa-key.private_key_pem
  file_permission = "0600"
}

resource "null_resource" "ansible_jenkins" {

  provisioner "remote-exec" {
    connection {
      host = oci_core_instance.jenkins_instance.public_ip
      user = "opc"
      private_key = tls_private_key.rsa-key.private_key_openssh
    }
    inline = ["echo 'connected!'"]
  }

  provisioner "local-exec" {
    command = "chmod +x ./run.sh && ./run.sh"
    environment = {
      HOST = oci_core_instance.jenkins_instance.public_ip
      JENKINS_ADMIN_PWD = var.jenkins_admin_password
      JENKINS_PORT = var.jenkins_port
    }
    working_dir = "${path.root}/jenkins-playbook"
  }

  triggers = {
    ansible_rerun = var.ansible_rerun ? timestamp() : null
  }

}