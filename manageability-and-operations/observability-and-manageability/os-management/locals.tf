
locals {
  # availability_domain_name is set by OCI Resource Manager
  #availability_domain_number = tonumber(var.availability_domain) <= length(data.oci_identity_availability_domains.ads.availability_domains) ? tonumber(var.availability_domain) - 1 : 0
  #availability_domain_name = data.oci_identity_availability_domains.ads.availability_domains[local.availability_domain_number].name
  availability_domain_name = data.oci_identity_availability_domains.ads.availability_domains.0.name
  os_images = {
    "OracleLinux8" = data.oci_core_images.OracleLinux8.images.0.id
    "OracleLinux9" = data.oci_core_images.OracleLinux9.images.0.id
    "Ubuntu20"     = data.oci_core_images.Ubuntu20.images.0.id
    "Ubuntu22"     = data.oci_core_images.Ubuntu22.images.0.id
    "Windows2019"  = data.oci_core_images.Windows2019.images.0.id
  }

  # golden instances
  golden_instances = [
    {name = "OL8GoldenInstance1", os = var.mig1_os, subnet = "public", state = var.gi_state},
    {name = "OL8GoldenInstance2", os = var.mig2_os, subnet = "public", state = var.gi_state},
    {name = "OL9GoldenInstance1", os = var.mig3_os, subnet = "public", state = var.gi_state},
    {name = "OL9GoldenInstance2", os = var.mig4_os, subnet = "public", state = var.gi_state},
  ]

  # description of managed instance groups and managed instances
  mservers = [
      {group = var.mig1_name,  name = var.mig1_miname, os = var.mig1_os, subnet = "public", state=var.mi_state, count = var.mig1_count},
      {group = var.mig2_name,  name = var.mig2_miname, os = var.mig2_os, subnet = "public", state=var.mi_state, count = var.mig2_count},
      {group = var.mig3_name,  name = var.mig3_miname, os = var.mig3_os, subnet = "public", state=var.mi_state, count = var.mig3_count},
      {group = var.mig4_name,  name = var.mig4_miname, os = var.mig4_os, subnet = "public", state=var.mi_state, count = var.mig4_count},
      {group = "Windows_ManagedInstanceGroup",        name = "Windows2019", os = "Windows2019",  subnet = "public", state=var.mi_state, count = 0},
    ]

  servers = flatten([
    for server in local.mservers : [
      for i in range(1, server.count+1) : {
        group   = server.group
        name    = "${server.name}-${i}"
        os      = server.os
        subnet  = server.subnet
        state   = server.state
        item_no = "${server.os} no.: ${i} out of ${server.count}"
      }
    ]
  ])

}


