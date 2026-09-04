"""Application configuration."""
import logging
import subprocess
from functools import cached_property
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        ignored_types=(cached_property,),
    )

    # GitHub integration
    github_org: str = ""
    github_token: str = ""  # Fallback, prefer OAuth user token

    # GitHub App user-to-server OAuth (https://github.com/settings/developers)
    github_client_id: str = ""
    github_client_secret: str = ""
    github_auth_mode: Literal["github_app", "oauth_app"] = "github_app"
    github_writes_v2: bool = True
    github_api_timeout_seconds: float = 20.0

    # Session
    session_secret: str = "change-this-in-production-use-random-string"

    # Git configuration
    git_author_name: str = "Multi Cloud Control Plane"
    git_author_email: str = "gitops@example.com"

    # Application settings
    # Hosting platforms commonly set HOST and PORT.
    app_host: str = Field(default="0.0.0.0", validation_alias=AliasChoices("APP_HOST", "HOST"))
    app_port: int = Field(default=8011, validation_alias=AliasChoices("APP_PORT", "PORT"))
    app_url: str = "http://localhost:8011"  # Browser origin allowed by CORS

    # Default values for operations
    default_cloud: str = "oci"
    default_region: str = "eu-frankfurt-1"
    default_cloud_regions: str = "oci:eu-frankfurt-1;azure:westeurope;gcp:europe-west2"
    cloud_region_options: str = (
        "oci:eu-frankfurt-1,us-phoenix-1,us-ashburn-1,uk-london-1;"
        "azure:westeurope;"
        "gcp:europe-west2,europe-west4,us-east4"
    )

    # Small, non-secret MCCP installation configuration.
    mccp_installation_path: str = "mccp-installation.json"

    # Audit behavior
    audit_infra_paths: str = "oci/,azure/,gcp/"

    @cached_property
    def audit_infra_prefixes(self) -> list[str]:
        """Infrastructure path prefixes used to identify GitOps-relevant changes."""
        prefixes = [p.strip() for p in self.audit_infra_paths.split(",") if p.strip()]
        return prefixes or ["oci/", "azure/", "gcp/"]

    @staticmethod
    def _parse_cloud_region_list(value: str) -> dict[str, list[str]]:
        """Parse strings like 'oci:eu-frankfurt-1,us-phoenix-1;azure:westeurope'."""
        parsed: dict[str, list[str]] = {}
        for item in (value or "").split(";"):
            if ":" not in item:
                continue
            cloud, regions = item.split(":", 1)
            cloud_key = cloud.strip().lower()
            region_values = [region.strip() for region in regions.split(",") if region.strip()]
            if cloud_key and region_values:
                parsed[cloud_key] = region_values
        return parsed

    @cached_property
    def _default_regions_by_cloud(self) -> dict[str, list[str]]:
        return self._parse_cloud_region_list(self.default_cloud_regions)

    @cached_property
    def _region_options_by_cloud(self) -> dict[str, list[str]]:
        return self._parse_cloud_region_list(self.cloud_region_options)

    def default_region_for_cloud(self, cloud: str) -> str:
        """Return the configured default region for a cloud."""
        cloud_key = (cloud or "").strip().lower()
        regions = self._default_regions_by_cloud.get(cloud_key)
        return regions[0] if regions else self.default_region

    def region_options_for_cloud(self, cloud: str) -> list[str]:
        """Return selectable regions for a cloud, with the default first."""
        cloud_key = (cloud or "").strip().lower()
        default_region = self.default_region_for_cloud(cloud_key)
        options = self._region_options_by_cloud.get(cloud_key) or [default_region]
        return [default_region, *[region for region in options if region != default_region]]


logger = logging.getLogger(__name__)
settings = Settings()


def _load_gh_fallback_token() -> str:
    """Return a token from `gh auth token` if available, else empty string.

    Invoked lazily (e.g. from GitHubClient.__init__) so app import does not
    block on a 5s subprocess timeout when `gh` is missing or hangs.
    """
    try:
        result = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True, text=True, timeout=5
        )
        gh_token = result.stdout.strip()
        if gh_token and len(gh_token) > 30:
            return gh_token
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return ""


if settings.session_secret == "change-this-in-production-use-random-string":
    logger.warning("SESSION_SECRET is using the default value; set it in .env for production.")
