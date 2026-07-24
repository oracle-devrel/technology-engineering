# ─────────────────────────────────────────────────────────────
# main.tf – OCI resources for the gcplogs2oci pipeline
#
# Creates: Stream Pool, Stream, Log Analytics Log Group,
#          Connector Hub (Stream → Log Analytics).
#
# Log Analytics custom content (fields, parser, source) is NOT
# supported by the Terraform provider.  After applying this
# stack, run:
#   python3 stack/scripts/setup_log_analytics.py
# or the project-level scripts/setup_oci.sh (steps 5-6).
# ─────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 7.0"
    }
  }
}

# When run inside OCI Resource Manager, auth is automatic
# (resource principal).  Locally, the provider reads
# ~/.oci/config or TF_VAR / OCI_* environment variables.
provider "oci" {
  region = var.region
}

# ── Data Sources ──────────────────────────────────────────────

data "oci_log_analytics_namespaces" "this" {
  compartment_id = var.tenancy_ocid
}

locals {
  la_namespace = (
    var.log_analytics_namespace != ""
    ? var.log_analytics_namespace
    : try(
        data.oci_log_analytics_namespaces.this.namespace_collection[0].items[0].namespace,
        ""
      )
  )
}

# ── 1. Stream Pool ────────────────────────────────────────────

resource "oci_streaming_stream_pool" "gcp_pool" {
  compartment_id = var.compartment_ocid
  name           = var.stream_pool_name

  kafka_settings {
    auto_create_topics_enable = false
    num_partitions            = var.stream_partitions
    log_retention_hours       = var.stream_retention_in_hours
  }
}

# ── 2. Stream ─────────────────────────────────────────────────

resource "oci_streaming_stream" "gcp_stream" {
  name               = var.stream_name
  partitions         = var.stream_partitions
  stream_pool_id     = oci_streaming_stream_pool.gcp_pool.id
  retention_in_hours = var.stream_retention_in_hours
}

# ── 3. Log Analytics Log Group ────────────────────────────────

resource "oci_log_analytics_log_analytics_log_group" "gcp_logs" {
  compartment_id = var.compartment_ocid
  namespace      = local.la_namespace
  display_name   = var.log_group_name
  description    = var.log_group_description

  lifecycle {
    precondition {
      condition     = local.la_namespace != ""
      error_message = "Log Analytics namespace could not be detected.  Ensure Log Analytics is onboarded, or set the log_analytics_namespace variable."
    }
  }
}

# ── 4. Connector Hub ─────────────────────────────────────────

resource "oci_sch_service_connector" "gcp_bridge" {
  compartment_id = var.compartment_ocid
  display_name   = var.sch_name
  description    = var.sch_description

  source {
    kind = "streaming"
    cursor {
      kind = "TRIM_HORIZON"
    }
    stream_id = oci_streaming_stream.gcp_stream.id
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = oci_log_analytics_log_analytics_log_group.gcp_logs.id
    log_source_identifier = "GCP Cloud Logging Logs"
  }
}
