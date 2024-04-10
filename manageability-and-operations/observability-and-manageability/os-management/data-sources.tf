# Source from https://registry.terraform.io/providers/hashicorp/oci/latest/docs/data-sources/identity_availability_domains
# <tenancy-ocid> is the compartment OCID for the root compartment.
# Use <tenancy-ocid> for the compartment OCID.
data oci_identity_availability_domains ads {
  compartment_id = var.tenancy_ocid
}

data oci_identity_compartment target_compartment {
  #id = "${file("../target_compartment_id.txt")}"
  id = var.compartment_ocid
}

# filter for the latest Oracle 8 image
data oci_core_images OracleLinux8 {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  filter {
    name = "display_name"
    values = ["^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-([\\.0-9-]+)$"]
    regex = true
  }
}

# filter for the latest Oracle 9 image
data oci_core_images OracleLinux9 {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "9"
  filter {
    name = "display_name"
    values = ["^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-([\\.0-9-]+)$"]
    regex = true
  }
}

# filter for the latest Ubuntu 20 image
data oci_core_images Ubuntu20 {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "20.04"
  filter {
    name = "display_name"
    values = ["^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-([\\.0-9-]+)$"]
    regex = true
  }
}

# filter for the latest Ubuntu 22 image
data oci_core_images Ubuntu22 {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Canonical Ubuntu"
  operating_system_version = "22.04"
  filter {
    name = "display_name"
    values = ["^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-([\\.0-9-]+)$"]
    regex = true
  }
}

# filter for the latest Windows Server 2019 image
data oci_core_images Windows2019 {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Windows"
  operating_system_version = "Server 2019 Standard"
  filter {
    name = "display_name"
    values = ["^Windows-Server-2019-Standard-Edition-VM-([\\.0-9-]+)$"]
    regex = true
  }
}

# may and will be evaluated before instances have been fully provisioned
#data "oci_core_instances" "oracle_8_instances" {
#  compartment_id = var.compartment_ocid
#  filter {
#    name   = "source_details.source_id"
#    values = [local.os_images["OracleLinux8"]]
#  }
#  filter {
#    name   = "state"
#    values = ["RUNNING"]
#  }
#}
#
#data "oci_core_instances" "oracle_9_instances" {
#  compartment_id = var.compartment_ocid
#  filter {
#    name   = "source_details.source_id"
#    values = [local.os_images["OracleLinux9"]]
#  }
#  filter {
#    name   = "state"
#    values = ["RUNNING"]
#  }
#}
#
#data "oci_core_instances" "windows_instances" {
#  compartment_id = var.compartment_ocid
#  filter {
#    name   = "source_details.source_id"
#    values = [local.os_images["Windows2019"]]
#  }
#  filter {
#    name   = "state"
#    values = ["RUNNING"]
#  }
#}
