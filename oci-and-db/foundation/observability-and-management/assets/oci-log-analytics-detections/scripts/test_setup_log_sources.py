#!/usr/bin/env python3
"""Regression tests for custom Log Analytics field/parser/source contracts."""

import os
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import oci

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oci_config import SOURCE_CANDIDATE_GROUPS
from setup_log_sources import (
    APP_FIELD_MAPPINGS,
    APP_SOURCE_DISPLAY,
    APP_SOURCE_DESC,
    APP_SOURCE_INTERNAL,
    build_existing_field_map,
    build_field_reuse_audit,
    build_existing_field_inventory,
    FIELD_DATA_TYPE_OVERRIDES,
    CUSTOM_FIELDS,
    OCTO_APM_FIELD_DISPLAY_NAMES,
    OCTO_APM_WORKSHOP_FIELD_DISPLAY_NAMES,
    create_fields,
    create_source,
    custom_fields_for_octo_apm_workshop,
    field_mappings_for_octo_apm_workshop,
    missing_octo_apm_workshop_fields,
)


class TestSetupLogSources(unittest.TestCase):
    def test_application_source_and_parser_cover_octo_apm_fields(self):
        required_fields = {
            "Span ID": {"$.spanId", "$.span_id", "$.oracleApmSpanId"},
            "Parent Span ID": {"$.parentSpanId"},
            "Span Kind": {"$.spanKind"},
            "APM Domain": {"$.apmDomain"},
            "Metric Name": {"$.metricName"},
            "Metric Value": {"$.metricValue"},
            "Metric Unit": {"$.metricUnit"},
            "Service": {"$.serviceName", "$.service.name"},
            "Service Name": {"$.serviceName", "$.service.name"},
            "Service Namespace": {"$.service.namespace"},
            "Service Version": {"$.service.version"},
            "Service Instance ID": {"$.service.instance.id"},
            "Deployment Environment": {"$.deployment.environment"},
            "App Runtime": {"$.app.runtime"},
            "Trace ID": {"$.traceId", "$.trace_id", "$.oracleApmTraceId"},
            "Trace Parent": {"$.traceparent"},
            "Request ID": {"$.requestId", "$.request_id"},
            "Workflow ID": {"$.workflow_id"},
            "Workflow Step": {"$.workflow_step"},
            "HTTP Request Method": {"$.http.request.method", "$.http.method"},
            "URI Path": {"$.uriPath", "$.http.url.path"},
            "Response Code": {"$.statusCode", "$.http.status_code", "$.http.response.status_code"},
            "Response Time Ms": {"$.responseTimeMs", "$.http.response_time_ms"},
            "DB Target": {"$.dbTarget", "$.db.target"},
            "DB Statement": {"$.db.statement"},
            "DB Elapsed ms": {"$.db.elapsed_ms"},
            "DB Connection Name": {"$.db.connection_name"},
            "Java APM Path": {"$.java_apm.path"},
            "Java APM Status Code": {"$.java_apm.status_code"},
            "Java APM Latency ms": {"$.java_apm.latency_ms"},
            "Java APM Error Type": {"$.java_apm.error_type"},
            "Attack ID": {"$.security.attack.id"},
            "Attack Stage": {"$.security.attack.stage"},
            "Security Severity": {"$.security.severity"},
            "MITRE Technique ID": {"$.mitre.technique_id"},
            "MITRE Tactic": {"$.mitre.tactic"},
            "OSQuery Query": {"$.osquery.query"},
            "OSQuery Finding": {"$.osquery.finding"},
            "Compromised VM": {"$.vm.compromised"},
            "Payment Interception": {"$.payment.interception.detected"},
            "Payment Redirect": {"$.payment.redirect.detected"},
            "Payment Redirect URL": {"$.payment.redirect.url"},
            "Payment Risk Score": {"$.payment.risk_score"},
            "Process Command Line": {"$.process.command_line"},
            "Instance OCID": {"$.cloud.instance.id"},
            "Run ID": {"$.run_id"},
            "Attack Entry Point": {"$.attack.entry_point"},
            "LOTL Binary": {"$.attack.lotl_binary"},
            "Network Bytes Out": {"$.network.bytes_out"},
            "Severity": {"$.level", "$.severity"},
            "User ID (hashed)": {"$.user_id_hash"},
            "Business ID": {"$.business_id"},
            "API Gateway Name": {"$.oci.api_gateway.name"},
            "API Gateway Scope": {"$.oci.api_gateway.scope"},
            "API Gateway Deployment ID": {"$.oci.api_gateway.deployment_id"},
            "API Gateway Route": {"$.oci.api_gateway.route"},
            "API Gateway Route ID": {"$.oci.api_gateway.route_id"},
            "API Gateway Route Family": {"$.oci.api_gateway.route_family"},
            "API Gateway Request ID": {"$.oci.api_gateway.request_id"},
            "API Gateway Action": {"$.oci.api_gateway.action"},
            "API Gateway Policy Decision": {"$.oci.api_gateway.policy.decision"},
            "API Gateway Latency ms": {"$.oci.api_gateway.latency_ms"},
            "API Gateway Rate Limit": {"$.oci.api_gateway.rate_limit.limit"},
            "API Gateway Rate Remaining": {"$.oci.api_gateway.rate_limit.remaining"},
            "API Gateway Threat Signal": {"$.oci.api_gateway.threat_signal"},
        }
        mappings_by_field = {}
        for field_name, json_path, _sequence in APP_FIELD_MAPPINGS:
            mappings_by_field.setdefault(field_name, set()).add(json_path)

        self.assertEqual(APP_SOURCE_DISPLAY, "SOC Application Logs")
        self.assertEqual(SOURCE_CANDIDATE_GROUPS["application_logs"][0], "SOC Application Logs")
        for field_name, json_paths in required_fields.items():
            self.assertIn(field_name, CUSTOM_FIELDS)
            self.assertTrue(
                json_paths.issubset(mappings_by_field.get(field_name, set())),
                f"{field_name} missing mappings {json_paths - mappings_by_field.get(field_name, set())}",
            )

    def test_octo_apm_field_inventory_is_backed_by_custom_fields_and_parser(self):
        mapped_fields = {
            field_name
            for field_name, _json_path, _sequence in APP_FIELD_MAPPINGS
            if field_name not in {"msg", "time"}
        }
        for field_name in OCTO_APM_FIELD_DISPLAY_NAMES:
            self.assertIn(field_name, CUSTOM_FIELDS)
            self.assertIn(field_name, mapped_fields)

    def test_octo_apm_workshop_scope_is_minimal_and_required_field_first(self):
        fields = custom_fields_for_octo_apm_workshop()
        mappings = field_mappings_for_octo_apm_workshop()
        mapped_fields = {field_name for field_name, _json_path, _sequence in mappings}

        self.assertEqual(fields, list(OCTO_APM_WORKSHOP_FIELD_DISPLAY_NAMES))
        self.assertIn("msg", mapped_fields)
        self.assertIn("time", mapped_fields)
        self.assertIn("API Gateway Threat Signal", mapped_fields)
        self.assertIn("Payment Redirect URL", mapped_fields)
        self.assertIn("Severity Level", mapped_fields)
        self.assertNotIn("Client IP", fields)
        self.assertNotIn("API Gateway Name", fields)
        self.assertNotIn("Chaos Scenario", fields)

    def test_octo_apm_workshop_readiness_reports_missing_fields(self):
        field_map = {
            "Service Name": "udf_service_name",
            "service name": "udf_service_name",
        }

        missing = missing_octo_apm_workshop_fields(field_map)

        self.assertNotIn("Service Name", missing)
        self.assertIn("API Gateway Threat Signal", missing)

    def test_numeric_octo_fields_have_type_overrides_for_new_tenancies(self):
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["HTTP Status Code"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["DB Elapsed ms"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["Java APM Latency ms"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["Payment Risk Score"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["Network Bytes Out"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["API Gateway Latency ms"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["API Gateway Rate Limit"], "LONG")
        self.assertEqual(FIELD_DATA_TYPE_OVERRIDES["API Gateway Rate Remaining"], "LONG")

    def test_create_fields_creates_missing_fields_with_type_overrides(self):
        created_details = []

        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[]),
                    headers={},
                )

            def upsert_field(self, _namespace, details):
                created_details.append(details)
                return SimpleNamespace(
                    data=SimpleNamespace(
                        name=f"udf_{details.display_name.lower().replace(' ', '_')}",
                    )
                )

        result = create_fields(FakeClient(), "ns", ["HTTP Status Code", "Service Namespace"])

        self.assertEqual(result["HTTP Status Code"], "udf_http_status_code")
        self.assertEqual(created_details[0].data_type, "LONG")
        self.assertEqual(created_details[1].data_type, "String")

    def test_create_fields_reuses_exact_namespace_field_before_creating(self):
        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[
                        SimpleNamespace(
                            display_name="Service Namespace",
                            name="udf_service_namespace",
                            data_type="String",
                        )
                    ]),
                    headers={},
                )

            def upsert_field(self, _namespace, _details):
                raise AssertionError("existing exact fields must not be recreated")

        result = create_fields(FakeClient(), "ns", ["Service Namespace"])

        self.assertEqual(result["Service Namespace"], "udf_service_namespace")

    def test_existing_field_map_supports_display_and_internal_names(self):
        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[
                        SimpleNamespace(display_name="Trace ID", name="traceid"),
                    ]),
                    headers={},
                )

        result = build_existing_field_map(FakeClient(), "ns")

        self.assertEqual(result["Trace ID"], "traceid")
        self.assertEqual(result["trace id"], "traceid")
        self.assertEqual(result["traceid"], "traceid")

    def test_field_inventory_retries_transient_list_timeout(self):
        calls = []

        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                calls.append(True)
                if len(calls) == 1:
                    raise oci.exceptions.RequestException("read timed out")
                return SimpleNamespace(
                    data=SimpleNamespace(items=[
                        SimpleNamespace(display_name="Trace ID", name="traceid"),
                    ]),
                    headers={},
                )

        with patch("setup_log_sources.FIELD_LIST_ATTEMPTS", 2), patch("setup_log_sources.time.sleep"):
            inventory = build_existing_field_inventory(FakeClient(), "ns")

        self.assertEqual(len(calls), 2)
        self.assertEqual(inventory["by_display"]["Trace ID"]["name"], "traceid")

    def test_field_reuse_audit_reports_exact_missing_and_rewrite_candidates(self):
        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[
                        SimpleNamespace(display_name="Trace ID", name="traceid", data_type="String"),
                        SimpleNamespace(display_name="Service", name="service", data_type="String"),
                    ]),
                    headers={},
                )

        inventory = build_existing_field_inventory(FakeClient(), "ns")
        audit = build_field_reuse_audit(
            inventory,
            ["Trace ID", "Service Name", "Payment Redirect URL"],
        )

        self.assertEqual(audit["total_requested"], 3)
        self.assertEqual(audit["exact_reuse"][0]["existing_internal_name"], "traceid")
        self.assertEqual(audit["missing"], ["Service Name", "Payment Redirect URL"])
        self.assertEqual(audit["rewrite_candidates"][0]["requested_display_name"], "Service Name")
        self.assertTrue(audit["rewrite_candidates"][0]["query_rewrite_required"])

    def test_create_fields_retries_string_fields_as_multi_valued_when_quota_is_full(self):
        created_details = []

        class FakeClient:
            def list_fields(self, _namespace, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[]),
                    headers={},
                )

            def upsert_field(self, _namespace, details):
                created_details.append(SimpleNamespace(
                    display_name=details.display_name,
                    data_type=details.data_type,
                    is_multi_valued=details.is_multi_valued,
                ))
                if not details.is_multi_valued:
                    raise oci.exceptions.ServiceError(
                        400,
                        "LimitExceeded",
                        {},
                        "Max limit reached for single-valued STRING field",
                    )
                return SimpleNamespace(data=SimpleNamespace(name="udfm_service_namespace"))

        result = create_fields(FakeClient(), "ns", ["Service Namespace"])

        self.assertEqual(result["Service Namespace"], "udfm_service_namespace")
        self.assertEqual(len(created_details), 2)
        self.assertFalse(created_details[0].is_multi_valued)
        self.assertTrue(created_details[1].is_multi_valued)
        self.assertEqual(created_details[1].data_type, "String")

    def test_create_source_refreshes_existing_source_parser_binding(self):
        existing_source = SimpleNamespace(name=APP_SOURCE_DISPLAY, display_name=APP_SOURCE_DISPLAY)

        class FakeClient:
            def list_sources(self, _namespace, _compartment_id, **_kwargs):
                return SimpleNamespace(
                    data=SimpleNamespace(items=[existing_source]),
                    headers={},
                )

            def get_source(self, _namespace, _source_name, _compartment_id):
                return SimpleNamespace(data=existing_source, headers={"etag": "etag-123"})

        completed = SimpleNamespace(returncode=0, stderr="", stdout="")
        with patch("setup_log_sources.subprocess.run", return_value=completed) as run:
            create_source(
                FakeClient(),
                "ns",
                "ocid1.compartment.oc1..example",
                APP_SOURCE_INTERNAL,
                APP_SOURCE_DISPLAY,
                APP_SOURCE_DESC,
                "socApplicationJsonParser",
            )

        command = run.call_args.args[0]
        self.assertIn("--name", command)
        self.assertEqual(command[command.index("--name") + 1], APP_SOURCE_DISPLAY)
        self.assertIn("--if-match", command)
        self.assertEqual(command[command.index("--if-match") + 1], "etag-123")
        self.assertIn("--parsers", command)


if __name__ == "__main__":
    unittest.main()
