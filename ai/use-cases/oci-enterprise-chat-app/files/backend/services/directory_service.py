"""Runtime configuration and discovery checks for Microsoft Entra ID."""

import asyncio
import logging
import os
from datetime import datetime

import httpx

from models.directory import (
    DirectoryConfiguration,
    DirectoryConfigurationUpdate,
    DirectoryConnectionCheck,
)

logger = logging.getLogger(__name__)


class DirectoryService:
    """Keeps directory settings in memory and validates Entra OIDC discovery.

    Deployments can seed the settings using environment variables.  Runtime
    updates are deliberately not written to disk because a directory client
    secret must not be persisted in a source-controlled application volume.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._tenant_id: str | None = None
        self._client_id: str | None = None
        self._redirect_uri: str | None = None
        self._client_secret: str | None = None
        self._group_sync_enabled = False
        self._group_mappings = []
        self._configured_at: datetime | None = None
        self._updated_at: datetime | None = None
        self.load_from_environment()

    def load_from_environment(self) -> None:
        """Seed settings from deployment environment variables when present."""
        tenant_id = os.getenv("ENTRA_TENANT_ID", "").strip() or None
        client_id = os.getenv("ENTRA_CLIENT_ID", "").strip() or None
        redirect_uri = os.getenv("ENTRA_REDIRECT_URI", "").strip() or None
        client_secret = os.getenv("ENTRA_CLIENT_SECRET", "").strip() or None

        if tenant_id and client_id and redirect_uri:
            now = datetime.utcnow()
            self._tenant_id = tenant_id
            self._client_id = client_id
            self._redirect_uri = redirect_uri
            self._client_secret = client_secret
            self._group_sync_enabled = (
                os.getenv("ENTRA_GROUP_SYNC_ENABLED", "false").lower() == "true"
            )
            self._configured_at = now
            self._updated_at = now

    async def get_configuration(self) -> DirectoryConfiguration:
        """Return the directory state without ever returning the client secret."""
        async with self._lock:
            is_configured = bool(self._tenant_id and self._client_id and self._redirect_uri)
            authority = (
                f"https://login.microsoftonline.com/{self._tenant_id}/v2.0"
                if self._tenant_id
                else None
            )
            return DirectoryConfiguration(
                tenant_id=self._tenant_id,
                client_id=self._client_id,
                redirect_uri=self._redirect_uri,
                authority=authority,
                group_sync_enabled=self._group_sync_enabled,
                group_mappings=list(self._group_mappings),
                is_configured=is_configured,
                client_secret_configured=bool(self._client_secret),
                configured_at=self._configured_at,
                updated_at=self._updated_at,
            )

    async def update_configuration(
        self, update: DirectoryConfigurationUpdate
    ) -> DirectoryConfiguration:
        """Store a validated configuration; a missing secret preserves the current one."""
        async with self._lock:
            now = datetime.utcnow()
            self._tenant_id = update.tenant_id
            self._client_id = update.client_id
            self._redirect_uri = update.redirect_uri
            if update.client_secret is not None:
                self._client_secret = update.client_secret
            self._group_sync_enabled = update.group_sync_enabled
            self._group_mappings = list(update.group_mappings)
            self._configured_at = self._configured_at or now
            self._updated_at = now

        return await self.get_configuration()

    async def clear_configuration(self) -> None:
        """Clear runtime state.  Intended for test isolation."""
        async with self._lock:
            self._clear_configuration()

    def _clear_configuration(self) -> None:
        """Clear in-memory state when the caller already owns test isolation."""
        self._tenant_id = None
        self._client_id = None
        self._redirect_uri = None
        self._client_secret = None
        self._group_sync_enabled = False
        self._group_mappings = []
        self._configured_at = None
        self._updated_at = None

    async def test_connection(self) -> DirectoryConnectionCheck:
        """Validate Entra's public OpenID discovery document for the tenant."""
        configuration = await self.get_configuration()
        if not configuration.is_configured or not configuration.authority:
            raise ValueError("Microsoft Entra ID is not configured")

        discovery_url = f"{configuration.authority}/.well-known/openid-configuration"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(discovery_url)
                response.raise_for_status()
                metadata = response.json()

            required_fields = ("issuer", "authorization_endpoint", "token_endpoint")
            if not all(metadata.get(field) for field in required_fields):
                raise ValueError("OpenID discovery response is missing required endpoints")

            return DirectoryConnectionCheck(
                status="connected",
                message="Microsoft Entra ID OpenID discovery is reachable.",
                issuer=metadata["issuer"],
            )
        except (httpx.HTTPError, ValueError) as exc:
            logger.warning("Entra OpenID discovery failed: %s", exc)
            return DirectoryConnectionCheck(
                status="failed",
                message="Unable to validate Microsoft Entra ID OpenID discovery.",
            )


directory_service = DirectoryService()
