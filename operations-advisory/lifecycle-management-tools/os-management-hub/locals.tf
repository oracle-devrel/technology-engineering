locals {
  compartment    = data.oci_identity_compartments.all_compartments.compartments[0]
  os_images = {
    "OracleLinux8" = {
      "arm" = data.oci_core_images.ol8_arm_latest.images[0].id
      "amd" = data.oci_core_images.ol8_amd_latest.images[0].id
      "x86" = data.oci_core_images.ol8_intel_latest.images[0].id
    }
    "OracleLinux9" = {
      "arm" = data.oci_core_images.ol9_arm_latest.images[0].id
      "amd" = data.oci_core_images.ol9_amd_latest.images[0].id
      "x86" = data.oci_core_images.ol9_intel_latest.images[0].id 
    }
    "OracleLinux10" = {
      "arm" = data.oci_core_images.ol10_arm_latest.images[0].id
      "amd" = data.oci_core_images.ol10_amd_latest.images[0].id
      "x86" = data.oci_core_images.ol10_intel_latest.images[0].id
    }
  }

  shapes = {
    "arm" = "VM.Standard.A1.Flex"
    "amd" = "VM.Standard.E4.Flex"
    "x86" = "VM.Optimized3.Flex"
  }

  et_nsg   = oci_core_network_security_group.et_network_security_group
  http_nsg = oci_core_network_security_group.http_network_security_group
}
