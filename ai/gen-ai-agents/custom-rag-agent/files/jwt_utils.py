"""
Utility to encode, decode JWT tokens.

With these functions you can create a valid JWT token and decode (and check it is valid).

You need a shared JWT_SECRET (see config_private.py)

It is used in the implementation of the MCP server.

These function must be used if you are not using OCI Iam to issue the JWT token
"""

from datetime import datetime, timedelta
import jwt
from utils import get_console_logger
from config import DEBUG
from config_private import JWT_ALGORITHM, JWT_SECRET

logger = get_console_logger()


def create_jwt_token(user="test-user"):
    """
    create a JWT token
    """
    payload = {
        # subject (any string identifying the user)
        "sub": user,
        # token expires in one hour
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    # show how to create a valid JWT token
    _token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return _token


def verify_jwt_token(token: str) -> None:
    """
    Decode the jwt token.
    Raise an exception if the JWT token is invalid.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

        # here we should check the content of payload
        if DEBUG:
            logger.info("Payload from token: %s", payload)

        return payload
    except jwt.PyJWTError as exc:
        logger.error("Invalid token: %s", exc)
        raise ValueError("Unauthorized request!") from exc


def get_token_from_headers(headers: dict):
    """
    Extract the token from the HTTP headers
    # the header has the format: Bearer <token>
    """
    header_name = "authorization"
    _token = headers[header_name].split(" ")[-1]

    return _token
