"""Authentication API endpoints."""

import hashlib
import logging
import os
import secrets
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status

from models.user import (
    LoginRequest,
    LoginResponse,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    SessionData,
    User,
    UserInDB,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


def hash_password(password: str) -> str:
    """Simple password hashing for demo purposes."""
    return hashlib.sha256(password.encode()).hexdigest()


# Admin credentials are sourced from the environment so the live password is
# never committed to source control. Defaults preserve the demo login.
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# Sample users for testing and demonstration
SAMPLE_USERS: dict[str, UserInDB] = {
    ADMIN_USERNAME: UserInDB(
        id="user-001",
        username=ADMIN_USERNAME,
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=hash_password(ADMIN_PASSWORD),
        is_active=True,
        is_admin=True,
    ),
    "demo": UserInDB(
        id="user-002",
        username="demo",
        email="demo@example.com",
        full_name="Demo User",
        hashed_password=hash_password("demo123"),
        is_active=True,
    ),
    "analyst": UserInDB(
        id="user-003",
        username="analyst",
        email="analyst@example.com",
        full_name="Data Analyst",
        hashed_password=hash_password("analyst123"),
        is_active=True,
    ),
}

# In-memory session store (for demo purposes)
SESSIONS: dict[str, SessionData] = {}

# Session duration
SESSION_DURATION_HOURS = 24


def create_session(user: UserInDB) -> str:
    """Create a new session for a user.

    Args:
        user: The authenticated user.

    Returns:
        Session token.
    """
    token = secrets.token_urlsafe(32)
    session = SessionData(
        user_id=user.id,
        username=user.username,
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(hours=SESSION_DURATION_HOURS),
    )
    SESSIONS[token] = session
    logger.info(f"Session created for user: {user.username}")
    return token


def get_session(token: str) -> SessionData | None:
    """Get session data by token.

    Args:
        token: Session token.

    Returns:
        Session data if valid, None otherwise.
    """
    session = SESSIONS.get(token)
    if session is None:
        return None

    # Check expiration
    if session.expires_at and datetime.utcnow() > session.expires_at:
        del SESSIONS[token]
        return None

    return session


def invalidate_session(token: str) -> bool:
    """Invalidate a session.

    Args:
        token: Session token.

    Returns:
        True if session was invalidated, False if not found.
    """
    if token in SESSIONS:
        del SESSIONS[token]
        return True
    return False


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> User:
    """Dependency to get the current authenticated user.

    Args:
        authorization: Authorization header with Bearer token.

    Returns:
        The authenticated user.

    Raises:
        HTTPException: If not authenticated.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from session
    user_data = SAMPLE_USERS.get(session.username)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return User(
        id=user_data.id,
        username=user_data.username,
        email=user_data.email,
        full_name=user_data.full_name,
        is_active=user_data.is_active,
        is_admin=user_data.is_admin,
        created_at=user_data.created_at,
    )


# Optional dependency that returns None if not authenticated
async def get_optional_user(authorization: Annotated[str | None, Header()] = None) -> User | None:
    """Dependency to optionally get the current user.

    Args:
        authorization: Authorization header with Bearer token.

    Returns:
        The authenticated user or None.
    """
    if not authorization:
        return None

    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[User | None, Depends(get_optional_user)]


async def get_directory_admin(current_user: CurrentUser) -> User:
    """Require the application administrator for directory configuration changes."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Directory configuration requires an administrator account",
        )
    return current_user


DirectoryAdmin = Annotated[User, Depends(get_directory_admin)]


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
    description="Authenticate with username and password to get a session token.",
)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate a user and create a session.

    Args:
        request: Login credentials.

    Returns:
        Login response with session token.

    Raises:
        HTTPException: If credentials are invalid.
    """
    user = SAMPLE_USERS.get(request.username)

    if user is None or user.hashed_password != hash_password(request.password):
        logger.warning(f"Failed login attempt for user: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    token = create_session(user)

    return LoginResponse(
        token=token,
        user=User(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ),
        message="Login successful",
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="User logout",
    description="Invalidate the current session.",
)
async def logout(authorization: Annotated[str | None, Header()] = None) -> None:
    """Logout and invalidate the session.

    Args:
        authorization: Authorization header with Bearer token.
    """
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            invalidate_session(parts[1])
            logger.info("User logged out successfully")


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Get the currently authenticated user's information.",
)
async def get_me(current_user: CurrentUser) -> User:
    """Get the current user's information.

    Args:
        current_user: The authenticated user.

    Returns:
        User information.
    """
    return current_user


@router.put(
    "/profile",
    response_model=User,
    summary="Update user profile",
    description="Update the current user's name and/or email.",
)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: CurrentUser,
) -> User:
    """Update the current user's profile fields.

    Args:
        request: Fields to update.
        current_user: The authenticated user.

    Returns:
        Updated user object.
    """
    user_in_db = SAMPLE_USERS.get(current_user.username)
    if user_in_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if request.full_name is not None:
        user_in_db.full_name = request.full_name
    if request.email is not None:
        user_in_db.email = request.email

    return User(
        id=user_in_db.id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        is_active=user_in_db.is_active,
        is_admin=user_in_db.is_admin,
        created_at=user_in_db.created_at,
    )


@router.post(
    "/change-password",
    response_model=dict,
    summary="Change password",
    description="Change the current user's password.",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser,
) -> dict:
    """Change the current user's password.

    Args:
        request: Current and new passwords.
        current_user: The authenticated user.

    Returns:
        Success message.

    Raises:
        HTTPException: If current password is incorrect or new password is invalid.
    """
    user_in_db = SAMPLE_USERS.get(current_user.username)
    if user_in_db is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user_in_db.hashed_password != hash_password(request.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 6 characters",
        )

    user_in_db.hashed_password = hash_password(request.new_password)
    logger.info(f"Password changed for user: {current_user.username}")

    return {"message": "Password changed successfully"}


@router.get(
    "/verify",
    response_model=dict,
    summary="Verify session",
    description="Verify if the current session is valid.",
)
async def verify_session(current_user: CurrentUser) -> dict:
    """Verify the current session is valid.

    Args:
        current_user: The authenticated user.

    Returns:
        Verification status.
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
    }
