"""Tests for GCP Cloud Audit Log schema fidelity.

Verified 2026-04-24 against `gcloud logging read logName:cloudaudit.googleapis.com`.
Pins the LogEntry + AuditLog proto shape so generator output matches real
exports via Cloud Logging API / Pub/Sub sink.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


class TestGcpAuditSchema:
    @pytest.fixture
    def sample(self):
        from schemas.gcp_audit_schema import build_gcp_audit_event
        return build_gcp_audit_event(
            event_time="2026-04-24T12:00:00.000Z",
            project_id="test-project",
            method_name="google.iam.admin.v1.SetIamPolicy",
            service_name="iam.googleapis.com",
            principal_email="user@example.com",
            caller_ip="203.0.113.1",
        )

    def test_top_level_log_entry_fields(self, sample):
        required = {
            "insertId", "logName", "resource", "severity", "timestamp",
            "receiveTimestamp", "labels", "protoPayload",
        }
        assert required.issubset(sample.keys())

    def test_log_name_format(self, sample):
        # Real format: projects/PROJECT/logs/cloudaudit.googleapis.com%2F{activity|data_access|system_event}
        assert sample["logName"].startswith("projects/test-project/logs/cloudaudit.googleapis.com%2F")

    def test_resource_shape(self, sample):
        assert "type" in sample["resource"]
        assert "labels" in sample["resource"]
        assert "project_id" in sample["resource"]["labels"]

    def test_proto_payload_audit_log_shape(self, sample):
        p = sample["protoPayload"]
        required = {
            "@type", "status", "authenticationInfo", "requestMetadata",
            "serviceName", "methodName", "authorizationInfo", "resourceName",
            "request", "response",
        }
        assert required.issubset(p.keys())
        assert p["@type"] == "type.googleapis.com/google.cloud.audit.AuditLog"

    def test_authentication_info(self, sample):
        auth = sample["protoPayload"]["authenticationInfo"]
        assert "principalEmail" in auth
        assert "principalSubject" in auth

    def test_request_metadata(self, sample):
        meta = sample["protoPayload"]["requestMetadata"]
        assert "callerIp" in meta
        assert "callerSuppliedUserAgent" in meta

    def test_authorization_info_list(self, sample):
        authz = sample["protoPayload"]["authorizationInfo"]
        assert isinstance(authz, list)
        assert len(authz) > 0
        first = authz[0]
        assert {"resource", "permission", "granted"}.issubset(first.keys())

    def test_status_shape(self, sample):
        s = sample["protoPayload"]["status"]
        assert {"code", "message"}.issubset(s.keys())

    def test_ocl_display_columns(self, sample):
        required = {
            "Log Source", "Event Name", "Method Name", "Service Name",
            "User Name", "Principal Email", "Source IP", "Client IP",
            "Project ID", "Resource Name", "Resource Type", "Severity",
        }
        assert required.issubset(sample.keys())

    def test_cloud_provider_tag(self, sample):
        assert sample["cloudProvider"] == "GCP"
        assert sample["log_source_identifier"] == "GCP Cloud Audit Logs"

    def test_generated_log_matches_schema(self):
        path = ROOT / "detection_logs" / "gcp_cloud_logging.jsonl"
        if not path.exists():
            pytest.skip("gcp_cloud_logging.jsonl not generated yet")
        with path.open() as f:
            events = [json.loads(line) for line in f]
        assert len(events) > 0
        # At least the GCP-category events must have the new shape;
        # cross-cloud emitters also go into this file — all must comply.
        for evt in events:
            assert evt["cloudProvider"] == "GCP"
            assert "protoPayload" in evt
            assert "methodName" in evt["protoPayload"]
            assert "serviceName" in evt["protoPayload"]
            assert "authenticationInfo" in evt["protoPayload"]
            assert "Log Source" in evt
            assert evt["Log Source"] == "GCP Cloud Audit Logs"
