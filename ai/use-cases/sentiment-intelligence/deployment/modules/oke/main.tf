# =============================================================================
# OKE Module — Kubernetes cluster and managed node pool
# =============================================================================

resource "oci_containerengine_cluster" "oke" {
  compartment_id     = var.compartment_ocid
  kubernetes_version = var.kubernetes_version
  name               = "${var.resource_prefix}-oke"
  vcn_id             = var.vcn_id
  freeform_tags      = var.freeform_tags

  cluster_pod_network_options {
    cni_type = "FLANNEL_OVERLAY"
  }

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = var.public_subnet_id
  }

  options {
    service_lb_subnet_ids = [var.public_subnet_id]

    add_ons {
      is_kubernetes_dashboard_enabled = false
      is_tiller_enabled               = false
    }
  }
}

# ---------- Node Pool ----------
data "oci_containerengine_node_pool_option" "node_pool_option" {
  node_pool_option_id = "all"
  compartment_id      = var.compartment_ocid
}

locals {
  # OKE image source names embed the Kubernetes version without the leading "v"
  # (e.g. "Oracle-Linux-8.9-...-OKE-1.30.1-..."), so strip it before matching.
  kubernetes_version_number = trimprefix(var.kubernetes_version, "v")

  # Ampere (A1/A2) shapes are ARM (aarch64); everything else here is x86_64.
  # The node image architecture must match the node shape or OKE rejects the
  # node pool with "Node shape and image are not compatible".
  node_is_arm = length(regexall("\\.A[0-9]+\\.", var.node_shape)) > 0

  # OKE images matching the selected Kubernetes version and node architecture,
  # excluding GPU images (incompatible with the standard flex shapes here).
  oke_images = [
    for src in data.oci_containerengine_node_pool_option.node_pool_option.sources :
    src if(
      src.source_type == "IMAGE" &&
      length(regexall("Oracle-Linux-[0-9]", src.source_name)) > 0 &&
      length(regexall("OKE-${local.kubernetes_version_number}(-|$)", src.source_name)) > 0 &&
      length(regexall("GPU", src.source_name)) == 0 &&
      (local.node_is_arm ?
        length(regexall("aarch64", src.source_name)) > 0 :
        length(regexall("aarch64", src.source_name)) == 0)
    )
  ]
}

resource "oci_containerengine_node_pool" "pool" {
  compartment_id     = var.compartment_ocid
  cluster_id         = oci_containerengine_cluster.oke.id
  kubernetes_version = var.kubernetes_version
  name               = "${var.resource_prefix}-node-pool"
  freeform_tags      = var.freeform_tags

  node_shape = var.node_shape

  node_shape_config {
    ocpus         = var.node_ocpus
    memory_in_gbs = var.node_memory_in_gbs
  }

  node_source_details {
    source_type = "IMAGE"
    image_id    = local.oke_images[0].image_id
  }

  node_config_details {
    size = var.node_pool_size

    placement_configs {
      availability_domain = var.availability_domain
      subnet_id           = var.private_subnet_id
    }

    freeform_tags = var.freeform_tags
  }

  initial_node_labels {
    key   = "app"
    value = var.resource_prefix
  }
}

# ---------- Kubeconfig ----------
data "oci_containerengine_cluster_kube_config" "kubeconfig" {
  cluster_id = oci_containerengine_cluster.oke.id
}
