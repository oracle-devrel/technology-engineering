"""Authenticated APIs for configuring Microsoft Entra ID."""

from fastapi import APIRouter, HTTPException, status

from models.directory import (
    DirectoryConfiguration,
    DirectoryConfigurationUpdate,
    DirectoryConnectionCheck,
)
from routers.auth import CurrentUser, DirectoryAdmin
from services.directory_service import directory_service

router = APIRouter(prefix="/api/auth/directory", tags=["directory"])


@router.get("", response_model=DirectoryConfiguration, summary="Get directory configuration")
async def get_directory_configuration(_current_user: CurrentUser) -> DirectoryConfiguration:
    """Return safe directory state for the signed-in user."""
    return await directory_service.get_configuration()


@router.put("", response_model=DirectoryConfiguration, summary="Configure directory")
async def update_directory_configuration(
    request: DirectoryConfigurationUpdate,
    _current_admin: DirectoryAdmin,
) -> DirectoryConfiguration:
    """Save Microsoft Entra OIDC settings.  Client secrets are write-only."""
    return await directory_service.update_configuration(request)


@router.post(
    "/test-connection",
    response_model=DirectoryConnectionCheck,
    summary="Test Microsoft Entra OpenID discovery",
)
async def test_directory_connection(
    _current_admin: DirectoryAdmin,
) -> DirectoryConnectionCheck:
    """Verify the configured tenant's public OIDC discovery document."""
    try:
        return await directory_service.test_connection()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
