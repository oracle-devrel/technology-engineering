"""Models for the Microsoft Entra ID directory integration."""

from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator, model_validator


class DirectoryGroupMapping(BaseModel):
    """Maps an Entra group object ID to an application role."""

    group_id: str = Field(..., min_length=1, max_length=200)
    role: str = Field(..., min_length=1, max_length=100)

    @field_validator("group_id", "role")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        """Reject values that are empty after whitespace is removed."""
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank")
        return value


class DirectoryConfiguration(BaseModel):
    """Safe-to-return state of the configured enterprise directory.

    The client secret is intentionally never included in this model.  The
    boolean lets administrators tell whether a confidential-client secret has
    been supplied without exposing it to the browser.
    """

    provider: Literal["microsoft_entra_id"] = "microsoft_entra_id"
    protocol: Literal["oidc"] = "oidc"
    tenant_id: str | None = None
    client_id: str | None = None
    redirect_uri: str | None = None
    authority: str | None = None
    group_sync_enabled: bool = False
    group_mappings: list[DirectoryGroupMapping] = Field(default_factory=list)
    is_configured: bool = False
    client_secret_configured: bool = False
    configured_at: datetime | None = None
    updated_at: datetime | None = None


class DirectoryConfigurationUpdate(BaseModel):
    """Administrator request to configure Microsoft Entra ID OIDC."""

    tenant_id: str = Field(..., min_length=1, max_length=255, pattern=r"^[A-Za-z0-9.-]+$")
    client_id: str = Field(..., min_length=1, max_length=255)
    redirect_uri: str = Field(..., min_length=1, max_length=2048)
    client_secret: str | None = Field(default=None, min_length=1, max_length=4096)
    group_sync_enabled: bool = False
    group_mappings: list[DirectoryGroupMapping] = Field(default_factory=list, max_length=100)

    @field_validator("tenant_id", "client_id", "redirect_uri")
    @classmethod
    def strip_required_fields(cls, value: str) -> str:
        """Normalize required string fields and reject blank values."""
        value = value.strip()
        if not value:
            raise ValueError("Value must not be blank")
        return value

    @field_validator("client_secret")
    @classmethod
    def strip_optional_secret(cls, value: str | None) -> str | None:
        """Treat an omitted secret as no secret update; do not retain whitespace."""
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Client secret must not be blank when provided")
        return value

    @field_validator("redirect_uri")
    @classmethod
    def validate_redirect_uri(cls, value: str) -> str:
        """Allow HTTPS redirects and local HTTP redirects used in development."""
        parsed_uri = urlsplit(value)
        is_local_http = parsed_uri.scheme == "http" and parsed_uri.hostname in {
            "localhost",
            "127.0.0.1",
            "::1",
        }
        if parsed_uri.scheme != "https" and not is_local_http:
            raise ValueError("Redirect URI must use HTTPS (or localhost HTTP for development)")
        if not parsed_uri.netloc:
            raise ValueError("Redirect URI must include a host")
        return value

    @model_validator(mode="after")
    def validate_group_sync_mappings(self) -> "DirectoryConfigurationUpdate":
        """Require a role mapping whenever group synchronization is enabled."""
        group_ids = [mapping.group_id.lower() for mapping in self.group_mappings]
        if len(group_ids) != len(set(group_ids)):
            raise ValueError("Group mappings must not contain duplicate group IDs")
        if self.group_sync_enabled and not self.group_mappings:
            raise ValueError("At least one group mapping is required when group sync is enabled")
        return self


class DirectoryConnectionCheck(BaseModel):
    """Result of checking the configured Entra OpenID discovery endpoint."""

    status: Literal["connected", "failed"]
    message: str
    issuer: str | None = None
    checked_at: datetime = Field(default_factory=datetime.utcnow)
