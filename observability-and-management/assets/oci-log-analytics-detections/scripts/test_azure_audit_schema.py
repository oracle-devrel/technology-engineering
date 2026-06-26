"""Tests for Azure audit schema fidelity against Azure Monitor export format.

Verified 2026-04-24 against Microsoft Graph `/v1.0/auditLogs/directoryAudits`
response and Azure Monitor Activity Log published schema. Pins three shapes:
SignInLogs, AuditLogs, Activity Log (ARM).
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


class TestAzureSchemas:
    @pytest.fixture
    def signin(self):
        from schemas.azure_audit_schema import build_azure_signin_event
        return build_azure_signin_event(
            event_time="2026-04-24T12:00:00.000Z",
            tenant_id="tenant-guid",
            user_principal_name="test@example.com",
            user_display_name="Test User",
            user_id="user-guid",
            app_id="app-guid",
            app_display_name="Microsoft Graph",
            ip_address="203.0.113.1",
        )

    @pytest.fixture
    def audit(self):
        from schemas.azure_audit_schema import build_azure_audit_event
        return build_azure_audit_event(
            event_time="2026-04-24T12:00:00.000Z",
            tenant_id="tenant-guid",
            operation_type="Add",
            activity_display_name="Add member to role",
            category="RoleManagement",
            initiator_upn="admin@example.com",
            initiator_id="admin-guid",
            initiator_ip="203.0.113.1",
            target_resource_upn="target@example.com",
        )

    @pytest.fixture
    def activity(self):
        from schemas.azure_audit_schema import build_azure_activity_event
        return build_azure_activity_event(
            event_time="2026-04-24T12:00:00.000Z",
            subscription_id="sub-guid",
            tenant_id="tenant-guid",
            caller="admin@example.com",
            caller_ip="203.0.113.1",
            operation_name="Microsoft.Storage/storageAccounts/write",
            resource_provider="Microsoft.Storage",
            resource_group="rg-test",
            resource_id="/subscriptions/sub-guid/resourceGroups/rg-test/providers/Microsoft.Storage/storageAccounts/test",
        )

    def test_signin_common_envelope(self, signin):
        required = {
            "time", "resourceId", "operationName", "operationVersion",
            "category", "tenantId", "resultType", "resultSignature",
            "durationMs", "callerIpAddress", "correlationId", "identity",
            "Level", "location", "properties",
        }
        assert required.issubset(signin.keys())
        assert signin["category"] == "SignInLogs"
        assert signin["operationName"] == "Sign-in activity"

    def test_signin_properties_shape(self, signin):
        props = signin["properties"]
        required = {
            "id", "createdDateTime", "userDisplayName", "userPrincipalName",
            "userId", "appId", "appDisplayName", "ipAddress", "status",
            "deviceDetail", "location", "riskLevelDuringSignIn",
        }
        assert required.issubset(props.keys())
        assert set(props["status"].keys()) == {"errorCode", "failureReason", "additionalDetails"}

    def test_audit_common_envelope(self, audit):
        assert audit["category"] == "AuditLogs"
        assert audit["operationName"] == "Add member to role"
        props = audit["properties"]
        required = {
            "id", "category", "correlationId", "result", "resultReason",
            "activityDisplayName", "activityDateTime", "loggedByService",
            "operationType", "initiatedBy", "targetResources", "additionalDetails",
        }
        assert required.issubset(props.keys())

    def test_audit_initiator_shape(self, audit):
        initiator = audit["properties"]["initiatedBy"]
        assert "user" in initiator and "app" in initiator
        user = initiator["user"]
        assert {"id", "displayName", "userPrincipalName", "ipAddress", "roles"}.issubset(user.keys())

    def test_activity_log_shape(self, activity):
        # Activity Log uses {value, localizedValue} objects for many fields
        assert isinstance(activity["operationName"], dict)
        assert set(activity["operationName"].keys()) == {"value", "localizedValue"}
        assert isinstance(activity["status"], dict)
        required = {
            "authorization", "caller", "channels", "correlationId",
            "eventDataId", "eventName", "category", "eventTimestamp",
            "id", "level", "operationId", "operationName", "resourceGroupName",
            "resourceProviderName", "resourceId", "status", "subscriptionId",
            "tenantId", "httpRequest",
        }
        assert required.issubset(activity.keys())

    def test_ocl_display_columns(self, signin, audit, activity):
        required = {
            "Log Source", "Event Name", "User Name", "Source IP",
            "Client IP", "Tenant ID", "Result Type", "Correlation ID",
        }
        for evt in (signin, audit, activity):
            assert required.issubset(evt.keys()), f"Missing OCL fields in {evt.get('category')}"

    def test_cloud_provider_tag(self, signin, audit, activity):
        for evt in (signin, audit, activity):
            assert evt["cloudProvider"] == "Azure"

    def test_generated_log_matches_schema(self):
        path = ROOT / "detection_logs" / "azure_entraid.jsonl"
        if not path.exists():
            pytest.skip("azure_entraid.jsonl not generated yet")
        with path.open() as f:
            events = [json.loads(line) for line in f]
        assert len(events) > 0
        seen_categories = set()
        for evt in events:
            assert evt["cloudProvider"] == "Azure"
            assert "Log Source" in evt
            assert "Tenant ID" in evt
            assert "Source IP" in evt
            cat = evt.get("category")
            cat_value = cat if isinstance(cat, str) else cat.get("value")
            seen_categories.add(cat_value)
        # Should cover all three Azure log shapes
        assert {"SignInLogs", "AuditLogs", "Administrative"}.issubset(seen_categories)
