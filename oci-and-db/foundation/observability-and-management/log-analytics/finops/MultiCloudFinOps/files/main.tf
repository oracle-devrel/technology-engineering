data "oci_objectstorage_namespace" "current" {
  compartment_id = var.tenancy_ocid
}

locals {
  oci_namespace     = coalesce(var.oci_namespace, data.oci_objectstorage_namespace.current.namespace)
  aws_ingest_prefix = trimsuffix(var.aws_ingest_prefix, "/")
  oci_ingest_prefix = trimsuffix(var.oci_ingest_prefix, "/")
  dashboard_import_ids = {
    dashboard_id                              = "ocid1.managementdashboard.oc1..aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    saved_search_compartment_service_usage_id = "ocid1.managementsavedsearch.oc1..aaaaaaaabbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    saved_search_consumption_analysis_id      = "ocid1.managementsavedsearch.oc1..aaaaaaaacccccccccccccccccccccccccccccccccccccccccccccccccccc"
    saved_search_anomaly_consumption_id       = "ocid1.managementsavedsearch.oc1..aaaaaaaadddddddddddddddddddddddddddddddddddddddddddddddddddd"
    saved_search_top_service_words_id         = "ocid1.managementsavedsearch.oc1..aaaaaaaaeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    saved_search_compartment_service_id       = "ocid1.managementsavedsearch.oc1..aaaaaaaaffffffffffffffffffffffffffffffffffffffffffffffffffff"
    saved_search_service_line_id              = "ocid1.managementsavedsearch.oc1..aaaaaaaagggggggggggggggggggggggggggggggggggggggggggggggggggg"
  }
}

# Preserve state from the earlier single-bucket version of this stack.
moved {
  from = oci_objectstorage_bucket.finops
  to   = oci_objectstorage_bucket.aws_focus
}

moved {
  from = oci_streaming_stream.object_collection
  to   = oci_streaming_stream.aws_object_collection
}

# The parser export is packaged with the Resource Manager stack. Log Analytics
# accepts custom-content imports as ZIP files, so Terraform builds that ZIP here.
data "archive_file" "focus_aws_content" {
  type        = "zip"
  output_path = "${path.module}/focus_aws_content.zip"

  source {
    content  = file("${path.module}/FOCUS_AWS.xml")
    filename = "FOCUS_AWS.xml"
  }
}

data "archive_file" "focus_oci_content" {
  type        = "zip"
  output_path = "${path.module}/focus_oci_content.zip"

  source {
    content  = file("${path.module}/FOCUS_OCI.xml")
    filename = "FOCUS_OCI.xml"
  }
}

resource "oci_log_analytics_namespace" "finops" {
  count = var.onboard_log_analytics ? 1 : 0

  namespace = local.oci_namespace
  # Log Analytics onboarding is scoped to the tenancy, not a child compartment.
  compartment_id = var.tenancy_ocid
  is_onboarded   = true
}

resource "oci_objectstorage_bucket" "aws_focus" {
  compartment_id        = var.compartment_ocid
  name                  = var.aws_ingest_bucket_name
  namespace             = local.oci_namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = true
}

resource "oci_objectstorage_bucket" "oci_focus" {
  compartment_id        = var.compartment_ocid
  name                  = var.oci_ingest_bucket_name
  namespace             = local.oci_namespace
  access_type           = "NoPublicAccess"
  object_events_enabled = true
}

resource "oci_streaming_stream" "aws_object_collection" {
  compartment_id     = var.compartment_ocid
  name               = "${var.name_prefix}-aws-object-collection"
  partitions         = 1
  retention_in_hours = 48
}

resource "oci_streaming_stream" "oci_object_collection" {
  compartment_id     = var.compartment_ocid
  name               = "${var.name_prefix}-oci-object-collection"
  partitions         = 1
  retention_in_hours = 48
}

resource "oci_log_analytics_log_analytics_log_group" "finops" {
  compartment_id = var.compartment_ocid
  namespace      = local.oci_namespace
  display_name   = "${var.name_prefix}-focus"
  description    = "FOCUS cost and usage data collected from Object Storage"

  depends_on = [oci_log_analytics_namespace.finops]
}

resource "oci_log_analytics_log_analytics_import_custom_content" "focus_aws" {
  namespace                  = local.oci_namespace
  import_custom_content_file = data.archive_file.focus_aws_content.output_path
  is_overwrite               = true

  depends_on = [oci_log_analytics_namespace.finops]
}

resource "oci_log_analytics_log_analytics_import_custom_content" "focus_oci" {
  namespace                  = local.oci_namespace
  import_custom_content_file = data.archive_file.focus_oci_content.output_path
  is_overwrite               = true

  depends_on = [oci_log_analytics_namespace.finops]
}

resource "oci_management_dashboard_management_dashboards_import" "finops_mc" {
  import_details = templatefile("${path.module}/FinOps_MC.json", merge({
    target_tenancy_id     = var.tenancy_ocid
    target_compartment_id = var.compartment_ocid
    oci_region            = var.oci_region
  }, local.dashboard_import_ids))
  override_dashboard_compartment_ocid    = var.compartment_ocid
  override_saved_search_compartment_ocid = var.compartment_ocid
  override_same_name                     = "true"
}

resource "oci_identity_dynamic_group" "object_collection" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-object-collection"
  description    = "Log Analytics Object Collection Rule resource principals"
  matching_rule  = "ALL {resource.type='loganalyticsobjectcollectionrule'}"
}

resource "oci_identity_policy" "object_collection_service" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-object-collection-service"
  description    = "Allow the Object Collection Rule to read FOCUS report objects"
  statements = [
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to read buckets in compartment id ${var.compartment_ocid}",
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to read objects in compartment id ${var.compartment_ocid}",
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to manage cloudevents-rules in compartment id ${var.compartment_ocid}",
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to inspect compartments in tenancy",
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to use tag-namespaces in tenancy where all {target.tag-namespace.name = /oracle-tags/}",
    "allow dynamic-group ${oci_identity_dynamic_group.object_collection.name} to {STREAM_CONSUME} in compartment id ${var.compartment_ocid}"
  ]
}

resource "oci_identity_policy" "collection_administrators" {
  compartment_id = var.tenancy_ocid
  name           = "${var.name_prefix}-collection-administrators"
  description    = "Allow FinOps administrators to manage this collection environment"
  statements = [
    "allow group ${var.oci_admin_group_name} to use loganalytics-features-family in tenancy",
    "allow group ${var.oci_admin_group_name} to use loganalytics-resources-family in compartment id ${var.compartment_ocid}",
    "allow group ${var.oci_admin_group_name} to use object-family in compartment id ${var.compartment_ocid}",
    "allow group ${var.oci_admin_group_name} to use stream-family in compartment id ${var.compartment_ocid}",
    "allow group ${var.oci_admin_group_name} to manage management-dashboard-family in compartment id ${var.compartment_ocid}"
  ]
}

resource "oci_log_analytics_log_analytics_object_collection_rule" "aws_focus" {
  namespace           = local.oci_namespace
  compartment_id      = var.compartment_ocid
  name                = "${var.name_prefix}-aws-focus"
  description         = "Collect AWS FOCUS CSV and CSV.GZ reports from Object Storage"
  os_namespace        = local.oci_namespace
  os_bucket_name      = oci_objectstorage_bucket.aws_focus.name
  log_group_id        = oci_log_analytics_log_analytics_log_group.finops.id
  log_source_name     = "FOCUS_AWS"
  collection_type     = "LIVE"
  stream_id           = oci_streaming_stream.aws_object_collection.id
  stream_cursor_type  = "LATEST"
  object_name_filters = ["${local.aws_ingest_prefix}/*"]

  depends_on = [
    oci_identity_policy.object_collection_service,
    oci_log_analytics_log_analytics_import_custom_content.focus_aws
  ]
}

resource "oci_log_analytics_log_analytics_object_collection_rule" "oci_focus" {
  namespace           = local.oci_namespace
  compartment_id      = var.compartment_ocid
  name                = "${var.name_prefix}-oci-focus"
  description         = "Collect OCI FOCUS CSV and CSV.GZ reports from Object Storage"
  os_namespace        = local.oci_namespace
  os_bucket_name      = oci_objectstorage_bucket.oci_focus.name
  log_group_id        = oci_log_analytics_log_analytics_log_group.finops.id
  log_source_name     = "FOCUS_OCI"
  collection_type     = "LIVE"
  stream_id           = oci_streaming_stream.oci_object_collection.id
  stream_cursor_type  = "LATEST"
  object_name_filters = ["${local.oci_ingest_prefix}/*"]

  depends_on = [
    oci_identity_policy.object_collection_service,
    oci_log_analytics_log_analytics_import_custom_content.focus_oci
  ]
}
