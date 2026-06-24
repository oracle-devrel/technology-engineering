# --- Data Sources ---

# Object Storage namespace
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.compartment_ocid
}

# Latest Oracle Linux 8 image
locals {
  regex_shape_amd = (var.instance_shape == "VM.Standard.x86.Generic") ? "^VM.Standard.E.*Flex$" : var.instance_shape
  regex_shape     = (var.instance_shape == "VM.Standard.A1.Flex") ? "^VM.Standard.A.*Flex$" : local.regex_shape_amd

  regex_amd_linux    = "^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-([\\.0-9-]+)$"
  regex_ampere_linux = "^([a-zA-z]+)-([a-zA-z]+)-([\\.0-9]+)-aarch64-([\\.0-9-]+)$"
  regex_linux        = (var.instance_shape == "VM.Standard.A1.Flex") ? local.regex_ampere_linux : local.regex_amd_linux
}

data "oci_core_images" "oraclelinux" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  filter {
    name   = "display_name"
    values = [local.regex_linux]
    regex  = true
  }
}

# Availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Shape availability per AD
data "oci_core_shapes" "filtered_shapes" {
  for_each = toset(data.oci_identity_availability_domains.ads.availability_domains[*].name)

  compartment_id      = var.compartment_ocid
  availability_domain = each.value

  filter {
    name   = "name"
    regex  = true
    values = [local.regex_shape]
  }
}

locals {
  available_domains = [
    for ad in data.oci_core_shapes.filtered_shapes : ad.availability_domain if length(ad.shapes) > 0
  ]
  filtered_shapes          = flatten([for ad in data.oci_core_shapes.filtered_shapes : [for shape in ad.shapes : shape.name]])
  availability_domain_name = local.available_domains[0]
  shape                    = reverse(sort(local.filtered_shapes))[0]
  object_storage_namespace = data.oci_objectstorage_namespace.ns.namespace
}

# OCI services (for service gateway)
data "oci_core_services" "all_services" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}
