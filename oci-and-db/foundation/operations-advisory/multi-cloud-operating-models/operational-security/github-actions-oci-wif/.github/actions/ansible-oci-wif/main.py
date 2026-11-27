#!/usr/bin/env python3
"""Create ephemeral RPST credentials for the OCI Ansible collection."""

from __future__ import annotations

import base64
import os
import pathlib
import tempfile
from urllib.parse import urlsplit


def required_env(name: str) -> str:
    """Return a required environment value without exposing its contents."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def required_config_value(name: str) -> str:
    """Reject values that could inject another OCI config setting."""
    value = required_env(name)
    if "\n" in value or "\r" in value:
        raise RuntimeError(f"Invalid value for environment variable: {name}")
    return value


def atomic_write(path: pathlib.Path, content: str | bytes) -> None:
    """Atomically write a protected credential file."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        if isinstance(content, bytes):
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        else:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        os.replace(temporary_name, path)
        os.chmod(path, 0o600)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def append_command_values(variable: str, values: dict[str, pathlib.Path | str]) -> None:
    """Append non-secret paths or environment settings to a GitHub command file."""
    command_file = os.environ.get(variable)
    if not command_file:
        return

    rendered_values = {name: str(value) for name, value in values.items()}
    if any("\n" in value or "\r" in value for value in rendered_values.values()):
        raise RuntimeError(f"Invalid value for GitHub command file: {variable}")

    with open(command_file, "a", encoding="utf-8") as stream:
        for name, value in rendered_values.items():
            stream.write(f"{name}={value}\n")


def exchange_rpst(source_token_path: pathlib.Path) -> tuple[str, bytes]:
    """Exchange the source JWT and a generated public key for an RPST."""
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives.serialization import Encoding, NoEncryption, PrivateFormat, PublicFormat
    from oci._vendor import requests

    domain_url = required_config_value("OCI_TOKEN_EXCHANGE_DOMAIN_URL").rstrip("/")
    parsed = urlsplit(domain_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.path or parsed.query or parsed.fragment or parsed.username:
        raise RuntimeError("Use an HTTPS Identity Domain base URL without a path")
    source_token = source_token_path.read_text(encoding="utf-8").strip()
    if not source_token:
        raise RuntimeError("OCI workload identity token file is empty")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = base64.b64encode(private_key.public_key().public_bytes(
        Encoding.DER, PublicFormat.SubjectPublicKeyInfo,
    )).decode("ascii")
    try:
        response = requests.post(
            domain_url + "/oauth2/v1/token",
            auth=(required_config_value("OCI_TOKEN_EXCHANGE_CLIENT_ID"),
                  required_config_value("OCI_TOKEN_EXCHANGE_CLIENT_SECRET")),
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "requested_token_type": "urn:oci:token-type:oci-rpst",
                "subject_token": source_token,
                "subject_token_type": "jwt",
                "public_key": public_key,
                "res_type": required_config_value("OCI_TOKEN_EXCHANGE_RESOURCE_TYPE"),
            },
            timeout=60, allow_redirects=False,
        )
        if not 200 <= response.status_code < 300:
            raise RuntimeError(f"RPST exchange failed: HTTP {response.status_code}")
        token = response.json().get("token")
        if not isinstance(token, str) or not token:
            raise RuntimeError("RPST exchange returned no token")
    except RuntimeError:
        raise
    except Exception:
        raise RuntimeError("RPST exchange failed; response suppressed") from None
    return token, private_key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())


def main() -> None:
    """Write protected RPST files for oracle.oci resource principal authentication."""
    runner_temp = pathlib.Path(required_env("RUNNER_TEMP")).resolve()
    if runner_temp == pathlib.Path("/"):
        raise RuntimeError("RUNNER_TEMP is not a safe runtime root")
    source_token_path = pathlib.Path(required_env("OCI_WORKLOAD_IDENTITY_TOKEN_PATH")).resolve()
    if not source_token_path.is_relative_to(runner_temp) or not source_token_path.is_file():
        raise RuntimeError("The source JWT must be a file below RUNNER_TEMP")
    region = required_config_value("OCI_REGION")
    credentials_dir = runner_temp / "oci-ansible-wif"
    if credentials_dir.is_symlink():
        raise RuntimeError("Credential directory must not be a symlink")
    token, private_key = exchange_rpst(source_token_path)
    rpst_path = credentials_dir / "rpst"
    private_key_path = credentials_dir / "private_key.pem"
    atomic_write(rpst_path, token)
    atomic_write(private_key_path, private_key)
    append_command_values("GITHUB_ENV", {
        "OCI_ANSIBLE_AUTH_TYPE": "resource_principal",
        "OCI_RESOURCE_PRINCIPAL_VERSION": "2.2",
        "OCI_RESOURCE_PRINCIPAL_RPST": rpst_path,
        "OCI_RESOURCE_PRINCIPAL_PRIVATE_PEM": private_key_path,
        "OCI_RESOURCE_PRINCIPAL_REGION": region,
    })
    append_command_values("GITHUB_OUTPUT", {
        "rpst_path": rpst_path,
        "private_key_path": private_key_path,
    })
    print("Ephemeral OCI Ansible RPST credentials created")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        raise SystemExit("Unable to create RPST credentials; check configuration and connectivity. Details suppressed.") from None
