locals {
  # vendor software sources
  ol10arm = data.oci_os_management_hub_software_sources.ol10arm_vendor_software_sources.software_source_collection.0.items
  ol9arm  = data.oci_os_management_hub_software_sources.ol9arm_vendor_software_sources.software_source_collection.0.items
  ol8arm  = data.oci_os_management_hub_software_sources.ol8arm_vendor_software_sources.software_source_collection.0.items
  ol10x86 = data.oci_os_management_hub_software_sources.ol10x86_vendor_software_sources.software_source_collection.0.items
  ol9x86  = data.oci_os_management_hub_software_sources.ol9x86_vendor_software_sources.software_source_collection.0.items
  ol8x86  = data.oci_os_management_hub_software_sources.ol8x86_vendor_software_sources.software_source_collection.0.items
#  # custom software sources
#  software_sources = {
#    ol10arm = { source = oci_os_management_hub_software_source.ol10arm["create"] }
#    ol9arm  = { source = oci_os_management_hub_software_source.ol9arm["create"] }
#    ol8arm  = { source = oci_os_management_hub_software_source.ol8arm["create"] }
#    ol10x86 = { source = oci_os_management_hub_software_source.ol10x86["create"] }
#    ol9x86  = { source = oci_os_management_hub_software_source.ol9x86["create"] }
#    ol8x86  = { source = oci_os_management_hub_software_source.ol8x86["create"] }
#  }
#snap  ol8arm_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol8arm_snap_from_vendor) : s.id
#snap  ]
#snap  ol9arm_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol9arm_snap_from_vendor) : s.id
#snap  ]
#snap  ol10arm_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol10arm_snap_from_vendor) : s.id
#snap  ]
#snap  ol8x86_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol8x86_snap_from_vendor) : s.id
#snap  ]
#snap  ol9x86_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol9x86_snap_from_vendor) : s.id
#snap  ]
#snap  ol10x86_snapshot_software_source_ids = [
#snap    for s in values(oci_os_management_hub_software_source.ol10x86_snap_from_vendor) : s.id
#snap  ]
  create_profile         = true
  create_software_source = true
  attach_to_ol10arm = {
    for k, v in var.instances : k => v
      if v.osmh && v.arch=="arm" && v.os=="OracleLinux10"
  }
  attach_to_ol10x86 = {
    for k, v in var.instances : k => v
      if v.osmh && (v.arch=="x86" || v.arch=="amd") && v.os=="OracleLinux10"
  }
  attach_to_ol9arm = {
    for k, v in var.instances : k => v
      if v.osmh && v.arch=="arm" && v.os=="OracleLinux9"
  }
  attach_to_ol9x86 = {
    for k, v in var.instances : k => v
      if v.osmh && (v.arch=="x86" || v.arch=="amd") && v.os=="OracleLinux9"
  }
  attach_to_ol8arm = {
    for k, v in var.instances : k => v
      if v.osmh && v.arch=="arm" && v.os=="OracleLinux8"
  }
  attach_to_ol8x86 = {
    for k, v in var.instances : k => v
      if v.osmh && (v.arch=="x86" || v.arch=="amd") && v.os=="OracleLinux8"
  }
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol10arm" {
  for_each            = local.attach_to_ol10arm
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol10arm-profile["create"].id
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol10x86" {
  for_each            = local.attach_to_ol10x86
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol10x86-profile["create"].id
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol9arm" {
  for_each            = local.attach_to_ol9arm
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol9arm-profile["create"].id
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol9x86" {
  for_each            = local.attach_to_ol9x86
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol9x86-profile["create"].id
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol8arm" {
  for_each            = local.attach_to_ol8arm
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol8arm-profile["create"].id
}

resource "oci_os_management_hub_managed_instance_attach_profile_management" "attach_to_ol8x86" {
  for_each            = local.attach_to_ol8x86
  #Required
  managed_instance_id = oci_core_instance.standard-instance[each.key].id
  profile_id          = oci_os_management_hub_profile.ol8x86-profile["create"].id
}

resource "oci_os_management_hub_profile" "ol10arm-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol10arm-profile"
  arch_type           = "AARCH64"
  os_family           = "ORACLE_LINUX_10"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol10arm"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol10arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

#resource "oci_os_management_hub_profile" "ol9arm-profile" {
#  for_each            = local.create_profile ? {create = true} : {}
#  compartment_id      = local.compartment.id
#  display_name        = "ol9arm-profile"
#  profile_type        = "SOFTWARESOURCE"
#  arch_type           = "AARCH64"
#  os_family           = "ORACLE_LINUX_9"
#  vendor_name         = "ORACLE"
#  registration_type   = "OCI_LINUX"
#
#  # Attach all snapshot software sources
#  software_source_ids = [
#    for s in oci_os_management_hub_software_source.ol9arm_snap_from_vendor :
#    s.id
#  ]
#
#  description = "Profile using snapshot software sources"
#}

resource "oci_os_management_hub_profile" "ol9arm-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol9arm-profile"
  arch_type           = "AARCH64"
  os_family           = "ORACLE_LINUX_9"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol9arm"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol9arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

resource "oci_os_management_hub_profile" "ol8arm-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol8arm-profile"
  arch_type           = "AARCH64"
  os_family           = "ORACLE_LINUX_8"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol8arm"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol8arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

resource "oci_os_management_hub_profile" "ol10x86-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol10x86-profile"
  arch_type           = "X86_64"
  os_family           = "ORACLE_LINUX_10"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol10x86"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol10x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

resource "oci_os_management_hub_profile" "ol9x86-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol9x86-profile"
  arch_type           = "X86_64"
  os_family           = "ORACLE_LINUX_9"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol9x86"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol9x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

resource "oci_os_management_hub_profile" "ol8x86-profile" {
  for_each            = local.create_profile ? {create = true} : {}
  compartment_id      = local.compartment.id
  display_name        = "ol8x86-profile"
  arch_type           = "X86_64"
  os_family           = "ORACLE_LINUX_8"
  vendor_name         = "ORACLE"
  profile_type        = "SOFTWARESOURCE"
  registration_type   = "OCI_LINUX"
  #software_source_ids = [local.software_sources["ol8x86"].source.id]
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol8x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]
}

#snapresource "oci_os_management_hub_software_source" "ol8arm_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol8arm_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}
#snap
#snapresource "oci_os_management_hub_software_source" "ol9arm_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol9arm_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}
#snap
#snapresource "oci_os_management_hub_software_source" "ol10arm_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol10arm_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}
#snap
#snapresource "oci_os_management_hub_software_source" "ol8x86_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol8x86_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}
#snap#output "custom_software_source_ids" {
#snap#  value = {
#snap#    for k, v in oci_os_management_hub_software_source.ol8x86_snap_from_vendor :
#snap#    k => {
#snap#      id           = v.id
#snap#      display_name = v.display_name
#snap#    }
#snap#  }
#snap#}
#snap
#snapresource "oci_os_management_hub_software_source" "ol9x86_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol9x86_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}
#snap
#snap#output "custom_software_source_ids" {
#snap#  value = {
#snap#    for k, v in oci_os_management_hub_software_source.ol9arm_snap_from_vendor :
#snap#    k => {
#snap#      id           = v.id
#snap#      display_name = v.display_name
#snap#    }
#snap#  }
#snap#}
#snap
#snapresource "oci_os_management_hub_software_source" "ol10x86_snap_from_vendor" {
#snap  for_each = {
#snap    for src in flatten([
#snap      for c in data.oci_os_management_hub_software_sources.ol10x86_vendor_software_sources.software_source_collection :
#snap      c.items
#snap    ]) : src.id => src
#snap  }
#snap
#snap  compartment_id               = local.compartment.id
#snap  display_name                 = "${each.value.display_name}-snap-${formatdate("YYYYMMDD", timestamp())}"
#snap  is_auto_resolve_dependencies = false
#snap  is_latest_content_only       = false
#snap  is_automatically_updated     = false
#snap
#snap  software_source_type     = "CUSTOM"
#snap  software_source_sub_type = "SNAPSHOT"
#snap
#snap  vendor_software_sources {
#snap    display_name = each.value.display_name
#snap    id           = each.value.id
#snap  }
#snap  lifecycle {
#snap    ignore_changes = [
#snap      display_name
#snap    ]
#snap  }
#snap  timeouts {
#snap    create = "1h"
#snap    delete = "1h"
#snap  }
#snap
#snap  description = "Custom snapshot of ${each.value.display_name}"
#snap}

## OL10ARM
#resource "oci_os_management_hub_software_source" "ol10arm" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol10arm"
#  description                  = "aarch64 default repositories plus developer epel"
#  arch_type                    = "AARCH64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol10arm
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}
#
## OL9ARM
#resource "oci_os_management_hub_software_source" "ol9arm" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol9arm"
#  description                  = "aarch64 default repositories plus developer epel"
#  arch_type                    = "AARCH64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol9arm
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}
#
## OL8ARM
#resource "oci_os_management_hub_software_source" "ol8arm" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol8arm"
#  description                  = "aarch64 default repositories plus developer epel"
#  arch_type                    = "AARCH64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol8arm
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}
#
## OL10X86_64
#resource "oci_os_management_hub_software_source" "ol10x86" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol10x86"
#  description                  = "x86_64 default repositories plus developer epel"
#  arch_type                    = "X86_64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol10x86
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}
#
## OL9X86_64
#resource "oci_os_management_hub_software_source" "ol9x86" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol9x86"
#  description                  = "x86_64 default repositories plus developer epel"
#  arch_type                    = "X86_64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol9x86
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}
#
## OL8X86_64
#resource "oci_os_management_hub_software_source" "ol8x86" {
#  for_each                     = local.create_software_source ? {create = true} : {}
#  compartment_id               = local.compartment.id
#  software_source_type         = "CUSTOM"
#  display_name                 = "ol8x86"
#  description                  = "x86_64 default repositories plus developer epel"
#  arch_type                    = "X86_64"
#  is_auto_resolve_dependencies = true
#  is_latest_content_only       = false
#  is_automatically_updated     = false
#  dynamic "vendor_software_sources" {
#    for_each = local.ol8x86
#    iterator = repo
#    content  {
#      display_name = repo.value.repo_id
#      id           = repo.value.id
#    }
#  }
#}

#resource "oci_os_management_hub_managed_instance_group" "osmh_group" {
#  for_each         = local.software_sources
#  compartment_id   = local.compartment.id
#  display_name     = "${each.key}-group"
#  os_family        = local.software_sources[each.key].source.os_family
#  arch_type        = local.software_sources[each.key].source.arch_type
#  software_source_ids = [local.software_sources[each.key].source.id]
#  vendor_name      = "ORACLE"
#  location         = "OCI_COMPUTE"
#  description      = "group for ${local.software_sources[each.key].source.os_family}, ${local.software_sources[each.key].source.arch_type}"
#}
 
#resource "oci_os_management_hub_managed_instance_group" "osmh_group" {
#  for_each         = var.groups
#  compartment_id   = local.compartment.id
#  display_name     = "${each.key}-group"
#  os_family        = each.value.os_family
#  arch_type        = each.value.arch_type
#  vendor_name      = each.value.vendor_name
#  software_source_ids = []
#  location         = "OCI_COMPUTE"
#  description      = "group for ${each.value.os_family}, ${each.value.arch_type}"
#}

resource "oci_os_management_hub_managed_instance_group" "ol8arm_group" {
  compartment_id = local.compartment.id
  display_name   = "ol8arm-group"
  arch_type      = "AARCH64"
  os_family      = "ORACLE_LINUX_8"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol8arm_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol8arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL8 ARM"
}
resource "oci_os_management_hub_managed_instance_group" "ol9arm_group" {
  compartment_id = local.compartment.id
  display_name   = "ol9arm-group"
  arch_type      = "AARCH64"
  os_family      = "ORACLE_LINUX_9"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol9arm_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol9arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL9 ARM"
}
resource "oci_os_management_hub_managed_instance_group" "ol10arm_group" {
  compartment_id = local.compartment.id
  display_name   = "ol10arm-group"
  arch_type      = "AARCH64"
  os_family      = "ORACLE_LINUX_10"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol10arm_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol10arm_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL10 ARM"
}
resource "oci_os_management_hub_managed_instance_group" "ol8x86" {
  compartment_id = local.compartment.id
  display_name   = "ol8x86-group"
  arch_type      = "X86_64"
  os_family      = "ORACLE_LINUX_8"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol8x86_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol8x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL8 x86"
}
resource "oci_os_management_hub_managed_instance_group" "ol9x86_group" {
  compartment_id = local.compartment.id
  display_name   = "ol9x86-group"
  arch_type      = "X86_64"
  os_family      = "ORACLE_LINUX_9"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol9x86_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol9x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL9 x86"
}
resource "oci_os_management_hub_managed_instance_group" "ol10x86_group" {
  compartment_id = local.compartment.id
  display_name   = "ol10x86-group"
  arch_type      = "X86_64"
  os_family      = "ORACLE_LINUX_10"
  vendor_name    = "ORACLE"
  location       = "OCI_COMPUTE"

  #software_source_ids = local.ol10x86_snapshot_software_source_ids
  software_source_ids = [
    for s in data.oci_os_management_hub_software_sources.ol10x86_vendor_software_sources.software_source_collection.0.items :
    s.id
  ]

  description = "Managed Instance Group for OL10 x86"
}
