# Validate the target compartment exists
data "oci_identity_compartment" "target" {
  id = var.compartment_id
}

# Discover the Log Analytics namespace for this tenancy
data "oci_log_analytics_namespaces" "this" {
  compartment_id = var.tenancy_ocid
}

locals {
  la_namespace = data.oci_log_analytics_namespaces.this.namespace_collection[0].items[0].namespace

  stream_definitions = {
    "soc-detection-oci-audit"       = { log_source = "OCI Audit Logs" }
    "soc-detection-cloud-guard"     = { log_source = "OCI Cloud Guard Problems" }
    "soc-detection-linux-audit"     = { log_source = "SOC Linux Syslog Logs" }
    "soc-detection-windows-sysmon"  = { log_source = "Windows Sysmon Operational Logs" }
  }
}
