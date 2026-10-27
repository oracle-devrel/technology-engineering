locals {
  # Resolved home region — fall back to the deployment region
  effective_home_region = var.home_region != "" ? var.home_region : var.region

  # Resource naming
  resource_prefix = "${var.app_name}-${var.environment}"

  # OCI GenAI endpoint construction
  genai_endpoint = var.genai_endpoint != "" ? var.genai_endpoint : "https://inference.generativeai.${var.genai_region}.oci.oraclecloud.com"

  # OCIR URL construction
  ocir_url = "${local.region_key}.ocir.io/${data.oci_objectstorage_namespace.ns.namespace}/${var.ocir_repo_name}"

  # Region key for OCIR (derived from the region identifier)
  region_key = lower(data.oci_identity_regions.regions.regions[index(
    data.oci_identity_regions.regions.regions[*].name, var.region
  )].key)

  # OKE cluster access
  cluster_endpoint       = yamldecode(module.oke.kubeconfig).clusters[0].cluster.server
  cluster_ca_certificate = base64decode(yamldecode(module.oke.kubeconfig).clusters[0].cluster["certificate-authority-data"])

  # Tags
  common_tags = merge(var.freeform_tags, {
    "Environment" = var.environment
  })
}

# Data sources
data "oci_objectstorage_namespace" "ns" {
  compartment_id = var.tenancy_ocid
}

data "oci_identity_regions" "regions" {}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}
