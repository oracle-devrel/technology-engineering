# Copyright (c) 2026 Oracle and/or its affiliates.
# Licensed under the Universal Permissive License v 1.0 as shown at https://oss.oracle.com/licenses/upl/

"""Refresh an Oracle Analytics Cloud downloaded tokens.json file."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import requests


DEFAULT_REFRESH_URL = os.getenv("OAC_TOKEN_REFRESH_URL", "").strip()


def main() -> None:
    """Parse arguments and refresh an OAC token file."""
    parser = argparse.ArgumentParser(
        description="Refresh an OAC downloaded tokens.json file."
    )
    parser.add_argument("tokens_file", type=Path)
    parser.add_argument("--refresh-url", default=DEFAULT_REFRESH_URL)
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()
    if not args.refresh_url:
        parser.error(
            "Provide --refresh-url or set OAC_TOKEN_REFRESH_URL, e.g. "
            "https://<your-oac-instance>.analytics.ocp.oraclecloud.com"
            "/api/dv/api/v1/tokens/token/refresh"
        )

    payload = refresh_tokens(
        tokens_file=args.tokens_file,
        refresh_url=args.refresh_url,
        save=not args.no_save,
    )
    print("status: refreshed")
    print("keys:", ", ".join(sorted(payload.keys())))
    print("has_accessToken:", bool(payload.get("accessToken")))
    print("has_refreshToken:", bool(payload.get("refreshToken")))
    print("expiresIn:", payload.get("expiresIn"))


def refresh_tokens(tokens_file: Path, refresh_url: str, save: bool) -> dict[str, Any]:
    """Refresh OAC tokens using an existing downloaded token file.

    Args:
        tokens_file: Path to a JSON file with accessToken and refreshToken.
        refresh_url: OAC token refresh endpoint.
        save: Whether to overwrite the file with the refreshed payload.

    Returns:
        Refreshed token payload.

    Raises:
        RuntimeError: If the token file does not contain required values.
        requests.HTTPError: If OAC rejects the refresh request.
    """
    tokens = json.loads(tokens_file.read_text(encoding="utf-8"))
    access_token = str(tokens.get("accessToken", "")).strip()
    refresh_token = str(tokens.get("refreshToken", "")).strip()
    if not access_token or not refresh_token:
        raise RuntimeError("tokens.json must contain accessToken and refreshToken.")

    response = requests.post(
        refresh_url,
        headers={
            "Authorization": f"Bearer {strip_bearer(access_token)}",
            "Content-Type": "text/plain",
        },
        data=refresh_token,
        timeout=45,
    )
    response.raise_for_status()
    payload = response.json()
    if save:
        tokens_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        tokens_file.chmod(0o600)
    return payload


def refresh_oac_tokens_from_file(
    *,
    token_file: Path,
    refresh_url: str = DEFAULT_REFRESH_URL,
    save: bool = True,
) -> dict[str, Any]:
    """Refresh OAC tokens from a downloaded token file.

    Thin keyword-only wrapper around ``refresh_tokens`` so callers (the React
    bridge and the direct probe) can import a stable name.
    """
    return refresh_tokens(tokens_file=token_file, refresh_url=refresh_url, save=save)


def strip_bearer(token: str) -> str:
    """Remove a Bearer prefix if the token was copied with one.

    Args:
        token: Access token string.

    Returns:
        Token without the Bearer prefix.
    """
    token = token.strip()
    if token.lower().startswith("bearer "):
        return token[7:].strip()
    return token


if __name__ == "__main__":
    main()
