# ─────────────────────────────────────────────────────────────
# main.tf – OCI resources for the azurelogs2oci pipeline
#
# Creates: Stream Pool, Stream, Log Analytics Log Group,
#          Service Connector Hub (Stream → Log Analytics).
#
# This stack is idempotent: it detects existing resources by name
# and reuses them instead of failing on duplicates.
#
# Log Analytics custom content (fields, parser, source) is NOT
# supported by the Terraform provider.  After applying this
# stack, run:
#   python3 stack/scripts/setup_log_analytics.py
# or the project-level scripts/setup_oci_log_analytics.sh
# (steps 5-6).
# ─────────────────────────────────────────────────────────────

terraform {
  required_version = ">= 1.2.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

# When run inside OCI Resource Manager, auth is automatic
# (resource principal).  Locally, the provider reads
# ~/.oci/config or TF_VAR / OCI_* environment variables.
provider "oci" {
  region = var.region
}

# ── Data Sources: Discover existing resources ─────────────────

# Log Analytics namespace (tenancy-level)
data "oci_log_analytics_namespaces" "this" {
  compartment_id = var.tenancy_ocid
}

# Existing stream pools in compartment (list query)
data "oci_streaming_stream_pools" "existing" {
  compartment_id = var.compartment_ocid
  name           = var.stream_pool_name
  state          = "ACTIVE"
}

# Get full stream pool details (including kafka_settings) if one exists
data "oci_streaming_stream_pool" "existing" {
  count          = length(try(data.oci_streaming_stream_pools.existing.stream_pools, [])) > 0 ? 1 : 0
  stream_pool_id = data.oci_streaming_stream_pools.existing.stream_pools[0].id
}

# Existing streams in compartment
data "oci_streaming_streams" "existing" {
  compartment_id = var.compartment_ocid
  name           = var.stream_name
  state          = "ACTIVE"
}

# Existing Log Analytics log groups
data "oci_log_analytics_log_analytics_log_groups" "existing" {
  compartment_id = var.compartment_ocid
  namespace      = local.la_namespace
  display_name   = var.log_group_name
}

# Existing Service Connectors
data "oci_sch_service_connectors" "existing" {
  compartment_id = var.compartment_ocid
  display_name   = var.sch_name
  state          = "ACTIVE"
}

# ── Locals: Determine what exists ─────────────────────────────

locals {
  # Log Analytics namespace
  la_namespace = (
    var.log_analytics_namespace != ""
    ? var.log_analytics_namespace
    : try(
      data.oci_log_analytics_namespaces.this.namespace_collection[0].items[0].namespace,
      ""
    )
  )

  # Check for existing resources
  existing_stream_pool_list = try(data.oci_streaming_stream_pools.existing.stream_pools[0], null)
  existing_stream_pool      = try(data.oci_streaming_stream_pool.existing[0], null)
  existing_stream           = try(data.oci_streaming_streams.existing.streams[0], null)
  existing_log_group = try(
    data.oci_log_analytics_log_analytics_log_groups.existing.log_analytics_log_group_summary_collection[0].items[0],
    null
  )
  existing_sch = try(data.oci_sch_service_connectors.existing.service_connector_collection[0].items[0], null)

  # Flags for conditional creation
  create_stream_pool = local.existing_stream_pool_list == null
  create_stream      = local.existing_stream == null
  create_log_group   = local.existing_log_group == null
  create_sch         = local.existing_sch == null

  # Resolved IDs (existing or newly created)
  stream_pool_id = local.create_stream_pool ? oci_streaming_stream_pool.azure_pool[0].id : local.existing_stream_pool_list.id
  stream_id      = local.create_stream ? oci_streaming_stream.azure_stream[0].id : local.existing_stream.id
  log_group_id   = local.create_log_group ? oci_log_analytics_log_analytics_log_group.azure_logs[0].id : local.existing_log_group.id
  sch_id         = local.create_sch ? oci_sch_service_connector.azure_bridge[0].id : local.existing_sch.id

  # Messaging endpoint
  stream_messages_endpoint = local.create_stream ? oci_streaming_stream.azure_stream[0].messages_endpoint : local.existing_stream.messages_endpoint

  # Kafka bootstrap servers (use singular data source for full details)
  kafka_bootstrap_servers = local.create_stream_pool ? oci_streaming_stream_pool.azure_pool[0].kafka_settings[0].bootstrap_servers : local.existing_stream_pool.kafka_settings[0].bootstrap_servers
}

# ── 1. Stream Pool ────────────────────────────────────────────

resource "oci_streaming_stream_pool" "azure_pool" {
  count = local.create_stream_pool ? 1 : 0

  compartment_id = var.compartment_ocid
  name           = var.stream_pool_name

  kafka_settings {
    auto_create_topics_enable = false
    num_partitions            = var.stream_partitions
    log_retention_hours       = var.stream_retention_in_hours
  }
}

# ── 2. Stream ─────────────────────────────────────────────────

resource "oci_streaming_stream" "azure_stream" {
  count = local.create_stream ? 1 : 0

  name               = var.stream_name
  partitions         = var.stream_partitions
  stream_pool_id     = local.stream_pool_id
  retention_in_hours = var.stream_retention_in_hours
}

# ── 3. Log Analytics Log Group ────────────────────────────────

resource "oci_log_analytics_log_analytics_log_group" "azure_logs" {
  count = local.create_log_group ? 1 : 0

  compartment_id = var.compartment_ocid
  namespace      = local.la_namespace
  display_name   = var.log_group_name
  description    = var.log_group_description

  lifecycle {
    precondition {
      condition     = local.la_namespace != ""
      error_message = "Log Analytics namespace could not be detected. Ensure Log Analytics is onboarded, or set the log_analytics_namespace variable."
    }
  }
}

# ── 4. Service Connector Hub ─────────────────────────────────

resource "oci_sch_service_connector" "azure_bridge" {
  count = local.create_sch ? 1 : 0

  compartment_id = var.compartment_ocid
  display_name   = var.sch_name
  description    = var.sch_description

  source {
    kind = "streaming"
    cursor {
      kind = "TRIM_HORIZON"
    }
    stream_id = local.stream_id
  }

  target {
    kind                  = "loggingAnalytics"
    log_group_id          = local.log_group_id
    log_source_identifier = "azureLogsSource"
  }
}
