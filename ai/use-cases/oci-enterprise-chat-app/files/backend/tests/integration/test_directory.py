"""Integration and service tests for Microsoft Entra ID configuration."""

from unittest.mock import patch

import httpx
import pytest
from fastapi.testclient import TestClient

from models.directory import DirectoryConfigurationUpdate
from routers.auth import ADMIN_USERNAME, SAMPLE_USERS, SESSIONS, create_session
from services.directory_service import directory_service


@pytest.fixture(autouse=True)
def reset_directory_state() -> None:
    """Keep the global in-memory directory service isolated between tests."""
    directory_service._clear_configuration()
    SESSIONS.clear()
    yield
    directory_service._clear_configuration()
    SESSIONS.clear()


def authenticated_headers(username: str) -> dict[str, str]:
    """Create an authorization header for one of the seeded demo users."""
    return {"Authorization": f"Bearer {create_session(SAMPLE_USERS[username])}"}


def valid_directory_payload(**overrides: object) -> dict[str, object]:
    """Return a valid Entra OIDC configuration request body."""
    payload: dict[str, object] = {
        "tenant_id": "contoso.onmicrosoft.com",
        "client_id": "11111111-2222-3333-4444-555555555555",
        "redirect_uri": "http://localhost:5173/auth/callback",
        "client_secret": "secret-value-that-must-not-be-returned",
        "group_sync_enabled": True,
        "group_mappings": [{"group_id": "11111111-aaaa-bbbb-cccc-111111111111", "role": "analyst"}],
    }
    payload.update(overrides)
    return payload


class TestDirectoryConfigurationEndpoints:
    """Tests for the browser-facing directory configuration API."""

    def test_requires_authentication(self, test_client: TestClient) -> None:
        """Directory state is not exposed to anonymous callers."""
        response = test_client.get("/api/auth/directory")

        assert response.status_code == 401

    def test_admin_can_configure_and_secret_is_redacted(self, test_client: TestClient) -> None:
        """An admin can configure OIDC without the API leaking the secret."""
        response = test_client.put(
            "/api/auth/directory",
            headers=authenticated_headers(ADMIN_USERNAME),
            json=valid_directory_payload(),
        )

        assert response.status_code == 200
        configuration = response.json()
        assert configuration["is_configured"] is True
        assert configuration["client_secret_configured"] is True
        assert (
            configuration["authority"]
            == "https://login.microsoftonline.com/contoso.onmicrosoft.com/v2.0"
        )
        assert configuration["group_sync_enabled"] is True
        assert configuration["group_mappings"] == [
            {"group_id": "11111111-aaaa-bbbb-cccc-111111111111", "role": "analyst"}
        ]
        assert "client_secret" not in configuration
        assert "secret-value-that-must-not-be-returned" not in response.text

        get_response = test_client.get("/api/auth/directory", headers=authenticated_headers("demo"))
        assert get_response.status_code == 200
        assert get_response.json()["client_id"] == valid_directory_payload()["client_id"]

    def test_non_admin_cannot_update_configuration(self, test_client: TestClient) -> None:
        """Only the seeded administrator can change enterprise identity settings."""
        response = test_client.put(
            "/api/auth/directory",
            headers=authenticated_headers("demo"),
            json=valid_directory_payload(),
        )

        assert response.status_code == 403
        assert "administrator" in response.json()["detail"].lower()

    def test_group_sync_requires_at_least_one_mapping(self, test_client: TestClient) -> None:
        """Invalid group-sync settings are rejected before any state changes."""
        response = test_client.put(
            "/api/auth/directory",
            headers=authenticated_headers(ADMIN_USERNAME),
            json=valid_directory_payload(group_mappings=[]),
        )

        assert response.status_code == 422
        assert "group mapping" in response.text.lower()

    def test_rejects_non_local_http_redirect_uri(self, test_client: TestClient) -> None:
        """HTTP redirects are limited to true localhost addresses in development."""
        response = test_client.put(
            "/api/auth/directory",
            headers=authenticated_headers(ADMIN_USERNAME),
            json=valid_directory_payload(redirect_uri="http://localhost.example.com/callback"),
        )

        assert response.status_code == 422
        assert "redirect uri" in response.text.lower()

    def test_test_connection_reports_not_configured(self, test_client: TestClient) -> None:
        """The connection test explains when there is no tenant to validate."""
        response = test_client.post(
            "/api/auth/directory/test-connection",
            headers=authenticated_headers(ADMIN_USERNAME),
        )

        assert response.status_code == 409
        assert response.json()["detail"] == "Microsoft Entra ID is not configured"


class TestDirectoryService:
    """Tests for the OpenID discovery check without contacting Microsoft."""

    @pytest.mark.asyncio
    async def test_connection_validates_required_openid_metadata(self) -> None:
        """A valid discovery document is reported as a connected directory."""
        await directory_service.update_configuration(
            DirectoryConfigurationUpdate.model_validate(valid_directory_payload())
        )

        class FakeAsyncClient:
            def __init__(self, timeout: float) -> None:
                self.timeout = timeout

            async def __aenter__(self) -> "FakeAsyncClient":
                return self

            async def __aexit__(self, *_args: object) -> None:
                return None

            async def get(self, url: str) -> httpx.Response:
                return httpx.Response(
                    200,
                    request=httpx.Request("GET", url),
                    json={
                        "issuer": "https://login.microsoftonline.com/tenant/v2.0",
                        "authorization_endpoint": "https://login.microsoftonline.com/authorize",
                        "token_endpoint": "https://login.microsoftonline.com/token",
                    },
                )

        with patch("services.directory_service.httpx.AsyncClient", FakeAsyncClient):
            result = await directory_service.test_connection()

        assert result.status == "connected"
        assert result.issuer == "https://login.microsoftonline.com/tenant/v2.0"
