# Source from https://registry.terraform.io/providers/hashicorp/oci/latest/docs/data-sources/identity_availability_domains
# <tenancy-ocid> is the compartment OCID for the root compartment.
# Use <tenancy-ocid> for the compartment OCID.
data oci_identity_availability_domains ads {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_compartments" "all_compartments" {
  compartment_id            = var.tenancy_ocid           # Usually the root compartment (tenancy OCID)
  compartment_id_in_subtree = true
  name                      = var.compartment_name
  state                     = "ACTIVE"
}

data "oci_objectstorage_namespace" "namespace" {}
output "objectstorage_namespace" {
  value = data.oci_objectstorage_namespace.namespace.namespace
}

# needed to check if bucket already exists
data "oci_objectstorage_bucket" "script_bucket" {
    #Required
  namespace = data.oci_objectstorage_namespace.namespace.namespace
  name      = var.bucket_name
}

############################################################
# aarch64 images
data "oci_core_images" "ol10_arm_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "10"
  shape                    = "VM.Standard.A1.Flex"    # shape must be compatible with aarch64/ARM
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol9_arm_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "9"
  shape                    = "VM.Standard.A1.Flex"    # shape must be compatible with aarch64/ARM
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol8_arm_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Standard.A1.Flex"    # shape must be compatible with aarch64/ARM
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

############################################################
# Intel images
data "oci_core_images" "ol10_intel_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "10"
  shape                    = "VM.Optimized3.Flex"    # shape must be compatible with Intel
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol9_intel_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "9"
  shape                    = "VM.Optimized3.Flex"    # shape must be compatible with Intel
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol8_intel_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Optimized3.Flex"    # shape must be compatible with Intel
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}


############################################################
# AMD images
data "oci_core_images" "ol10_amd_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "10"
  shape                    = "VM.Standard.E4.Flex"    # shape must be compatible with AMD
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol9_amd_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "9"
  shape                    = "VM.Optimized3.Flex"    # shape must be compatible with AMD
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

data "oci_core_images" "ol8_amd_latest" {
  compartment_id           = var.tenancy_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = "VM.Optimized3.Flex"    # shape must be compatible with AMD
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
  state                    = "AVAILABLE"
}

#output ol10_arm_latest {
#  value = format("%s: %s", data.oci_core_images.ol10_arm_latest.images[0].display_name,
#                           data.oci_core_images.ol10_arm_latest.images[0].id)
#}
#output ol9_arm_latest {
#  value = format("%s: %s", data.oci_core_images.ol9_arm_latest.images[0].display_name,
#                           data.oci_core_images.ol9_arm_latest.images[0].id)
#}
#output ol8_arm_latest {
#  value = format("%s: %s", data.oci_core_images.ol8_arm_latest.images[0].display_name,
#                           data.oci_core_images.ol8_arm_latest.images[0].id)
#}
#output ol10_intel_latest {
#  value = format("%s: %s", data.oci_core_images.ol10_intel_latest.images[0].display_name,
#                           data.oci_core_images.ol10_intel_latest.images[0].id)
#}
#output ol9_intel_latest {
#  value = format("%s: %s", data.oci_core_images.ol9_intel_latest.images[0].display_name,
#                           data.oci_core_images.ol9_intel_latest.images[0].id)
#}
#output ol8_intel_latest {
#  value = format("%s: %s", data.oci_core_images.ol8_intel_latest.images[0].display_name,
#                           data.oci_core_images.ol8_intel_latest.images[0].id)
#}
#output ol10_amd_latest {
#  value = format("%s: %s", data.oci_core_images.ol10_amd_latest.images[0].display_name,
#                           data.oci_core_images.ol10_amd_latest.images[0].id)
#}
#output ol9_amd_latest {
#  value = format("%s: %s", data.oci_core_images.ol9_amd_latest.images[0].display_name,
#                           data.oci_core_images.ol9_amd_latest.images[0].id)
#}
#output ol8_amd_latest {
#  value = format("%s: %s", data.oci_core_images.ol8_amd_latest.images[0].display_name,
#                           data.oci_core_images.ol8_amd_latest.images[0].id)
#}

#output "latest_ol9_aarch64_image_id" {
#  value = data.oci_core_images.ol9_arm_latest.images[0].id
#}

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
#  compartment_id = var.target_compartment_ocid
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
#  compartment_id = var.target_compartment_ocid
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
#  compartment_id = var.target_compartment_ocid
#  filter {
#    name   = "source_details.source_id"
#    values = [local.os_images["Windows2019"]]
#  }
#  filter {
#    name   = "state"
#    values = ["RUNNING"]
#  }
#}


############################################################
# OS Management Hub software sources

# OL10ARM
data "oci_os_management_hub_software_sources" "ol10arm_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["AARCH64"]
    os_family = ["ORACLE_LINUX_10"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      values = ["ol10_uekr8","ol10_addons","ol10_appstream","ol10_baseos_latest","ol10_ksplice","ol10_u1_developer_epel"]
    }
}

# OL9ARM
data "oci_os_management_hub_software_sources" "ol9arm_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["AARCH64"]
    os_family = ["ORACLE_LINUX_9"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      values = ["ol9_uekr8","ol9_addons","ol9_appstream","ol9_baseos_latest","ol9_ksplice","ol9_oci_included","ol9_developer_epel"]
    }
}

# OL8ARM
data "oci_os_management_hub_software_sources" "ol8arm_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["AARCH64"]
    os_family = ["ORACLE_LINUX_8"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      values = ["ol8_mysql84_community","ol8_mysql84_tools_community","ol8_mysql_connectors_community","ol8_uekr7","ol8_addons","ol8_appstream","ol8_baseos_latest","ol8_ksplice","ol8_oci_included","ol8_developer_epel"]
    }
}

# OL10X86_64
data "oci_os_management_hub_software_sources" "ol10x86_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["X86_64"]
    os_family = ["ORACLE_LINUX_10"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      values = ["ol10_uekr8","ol10_addons","ol10_appstream","ol10_baseos_latest","ol10_ksplice","ol10_u1_developer_epel"]
    }
}

# OL9X86_64
data "oci_os_management_hub_software_sources" "ol9x86_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["X86_64"]
    os_family = ["ORACLE_LINUX_9"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      values = ["ol9_uekr8","ol9_addons","ol9_appstream","ol9_baseos_latest","ol9_ksplice","ol9_developer_epel"]
    }
}

# OL8X86_64
data "oci_os_management_hub_software_sources" "ol8x86_vendor_software_sources" {
    compartment_id = var.tenancy_ocid
    arch_type = ["X86_64"]
    os_family = ["ORACLE_LINUX_8"]
    vendor_name = "ORACLE"
    filter {
      name = "repo_id"
      #values = ["ol8_mysql84_community","ol8_mysql84_tools_community","ol8_mysql_connectors_community","ol8_uekr7","ol8_addons","ol8_appstream","ol8_baseos_latest","ol8_ksplice","ol8_oci_included","ol8_developer_epel"]
      values = ["ol8_mysql84_community","ol8_mysql84_tools_community","ol8_mysql_connectors_community","ol8_uekr7","ol8_baseos_latest","ol8_ksplice","ol8_developer_epel"]
    }
}


## OL9ARM
#output "ol9arm_vendor_software_sources" {
#  value = data.oci_os_management_hub_software_sources.ol9arm_vendor_software_sources.software_source_collection.0.items[*].repo_id
#}
## OL8ARM
#output "ol8arm_vendor_software_sources" {
#  value = data.oci_os_management_hub_software_sources.ol8arm_vendor_software_sources.software_source_collection.0.items[*].repo_id
#}
## OL9X86_64
#output "ol9x86_vendor_software_sources" {
#  value = data.oci_os_management_hub_software_sources.ol9x86_vendor_software_sources.software_source_collection.0.items[*].repo_id
#}
## OL8X86_64
#output "ol8x86_vendor_software_sources" {
#  value = data.oci_os_management_hub_software_sources.ol8x86_vendor_software_sources.software_source_collection.0.items[*].repo_id
#}
