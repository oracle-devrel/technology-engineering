
data "oci_core_instance" "starter_bastion" {
  instance_id = oci_core_instance.starter_compute.id
}

locals {
  local_bastion_ip = data.oci_core_instance.starter_bastion.public_ip
}

output "bastion_ip" {
  value = local.local_bastion_ip
}