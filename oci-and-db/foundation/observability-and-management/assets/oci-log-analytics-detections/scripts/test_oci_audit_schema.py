"""Tests for OCI audit event schema fidelity against real API shape.

The schema was verified on 2026-04-24 against live output from
`oci audit event list` (CloudEvents v0.1 envelope, eventTypeVersion 2.0).
These tests pin the shape so future edits cannot silently drift away from
the real OCI Audit API format.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


class TestOciAuditSchema:
    @pytest.fixture
    def sample_event(self):
        from schemas.oci_audit_schema import build_oci_audit_event
        return build_oci_audit_event(
            "com.oraclecloud.identitycontrolplane.createpolicy",
            event_time="2026-04-24T12:00:00.000Z",
            principal_id="ocid1.user.oc1..test",
            principal_name="test.user@example.local",
            auth_type="natv",
            ip_address="203.0.113.1",
            compartment_id="ocid1.compartment.oc1..test",
            compartment_name="test-compartment",
            tenant_id="ocid1.tenancy.oc1..test",
        )

    def test_cloudevents_envelope(self, sample_event):
        assert sample_event["cloudEventsVersion"] == "0.1"
        assert sample_event["contentType"] == "application/json"
        assert sample_event["eventTypeVersion"] == "2.0"
        assert sample_event["eventType"] == "com.oraclecloud.identitycontrolplane.createpolicy"
        assert sample_event["source"] == "identitycontrolplane"

    def test_top_level_fields_match_real_api(self, sample_event):
        required_top = {
            "cloudEventsVersion", "contentType", "eventId", "eventTime",
            "eventType", "eventTypeVersion", "source", "data",
        }
        assert required_top.issubset(sample_event.keys())

    def test_data_envelope_fields(self, sample_event):
        data = sample_event["data"]
        required_data = {
            "additionalDetails", "availabilityDomain", "compartmentId",
            "compartmentName", "definedTags", "eventGroupingId", "eventName",
            "freeformTags", "identity", "request", "resourceId",
            "resourceName", "response", "stateChange",
        }
        assert required_data.issubset(data.keys())

    def test_identity_fields(self, sample_event):
        identity = sample_event["data"]["identity"]
        required_identity = {
            "authType", "callerId", "callerName", "consoleSessionId",
            "credentials", "ipAddress", "principalId", "principalName",
            "tenantId", "userAgent",
        }
        assert required_identity.issubset(identity.keys())

    def test_request_response_envelope(self, sample_event):
        data = sample_event["data"]
        assert set(data["request"].keys()) >= {"action", "headers", "id", "parameters", "path"}
        assert set(data["response"].keys()) >= {"headers", "message", "payload", "responseTime", "status"}
        assert set(data["stateChange"].keys()) == {"current", "previous"}

    def test_ocl_display_columns_populated(self, sample_event):
        # OCI Log Analytics parses raw audit into display-named columns.
        # Detection queries reference these, so they must be populated.
        ocl_fields = {
            "Log Source", "Event ID", "Event Type", "Event Name",
            "User Name", "Source IP", "Client IP", "Compartment Name",
            "Compartment OCID", "Principal Name", "Principal ID",
            "Tenant ID", "Type",
        }
        assert ocl_fields.issubset(sample_event.keys())

    def test_event_name_extracted_from_event_type(self, sample_event):
        assert sample_event["data"]["eventName"] == "createpolicy"
        assert sample_event["Event Name"] == "createpolicy"

    def test_generated_log_matches_schema(self):
        """Every event in detection_logs/oci_audit.jsonl must have the envelope."""
        path = ROOT / "detection_logs" / "oci_audit.jsonl"
        if not path.exists():
            pytest.skip("detection_logs/oci_audit.jsonl not generated yet")
        with path.open() as f:
            events = [json.loads(line) for line in f]
        assert len(events) > 0
        for evt in events:
            assert "cloudEventsVersion" in evt
            assert evt["cloudEventsVersion"] == "0.1"
            assert "eventType" in evt
            assert evt["eventType"].startswith("com.oraclecloud.")
            assert "data" in evt
            assert "identity" in evt["data"]
            assert "stateChange" in evt["data"]
            assert "Log Source" in evt
            assert evt["Log Source"] == "OCI Audit Logs"
