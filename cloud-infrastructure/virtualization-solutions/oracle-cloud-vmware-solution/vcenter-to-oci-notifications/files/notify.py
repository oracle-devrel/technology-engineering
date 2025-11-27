#!/usr/bin/env python3
"""
Publish a message to an OCI Notifications topic without using the OCI Python SDK.

The script signs the REST request manually, so only standard libraries plus
`requests` and `cryptography` are required, which are included in the standard vCenter build.
"""

from __future__ import annotations

import argparse
import base64
import configparser
import hashlib
import json
import os
import pathlib
import socket
import sys
import urllib.parse
from datetime import datetime, timezone

import requests
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


DEFAULT_CONFIG_PATH = pathlib.Path("/home/vpxd/config")
DEFAULT_HEADERS = [
    "(request-target)",
    "date",
    "host",
    "content-length",
    "content-type",
    "x-content-sha256",
]


def _rfc_1123_date() -> str:
    return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def _load_profile(config_path: pathlib.Path, profile: str) -> configparser.SectionProxy:
    parser = configparser.ConfigParser()
    if not parser.read(config_path):
        raise FileNotFoundError(f"Could not read OCI config file at {config_path}")
    if profile not in parser:
        raise KeyError(f"Profile '{profile}' not found in {config_path}")
    return parser[profile]


def _load_private_key(key_path: pathlib.Path, passphrase: str | None):
    data = key_path.expanduser().read_bytes()
    password = passphrase.encode("utf-8") if passphrase else None
    return serialization.load_pem_private_key(data, password=password)


def _build_signature(
    method: str,
    path_query: str,
    headers: dict[str, str],
    key_id: str,
    private_key,
) -> str:
    signing_string = "\n".join(
        f"{name}: {headers[name]}" if name != "(request-target)" else f"{name}: {method.lower()} {path_query}"
        for name in DEFAULT_HEADERS
    )
    signature = private_key.sign(
        signing_string.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    signature_b64 = base64.b64encode(signature).decode("ascii")
    headers_list = " ".join(DEFAULT_HEADERS)
    return (
        f'Signature version="1",keyId="{key_id}",algorithm="rsa-sha256",'
        f'headers="{headers_list}",signature="{signature_b64}"'
    )


def publish_message(
    topic_id: str,
    subject: str,
    body_text: str,
    message_type: str,
    config_section: configparser.SectionProxy,
    endpoint: str | None,
    passphrase: str | None,
) -> dict:
    region = config_section.get("region")
    if not region and not endpoint:
        raise ValueError("Region missing in config; supply --region or --endpoint")

    resolved_endpoint = endpoint or f"https://notification.{region}.oci.oraclecloud.com"
    url = urllib.parse.urljoin(
        resolved_endpoint.rstrip("/") + "/",
        f"20181201/topics/{topic_id}/messages",
    )
    parsed = urllib.parse.urlparse(url)
    path_query = parsed.path + (f"?{parsed.query}" if parsed.query else "")

    payload = {"title": subject, "body": body_text}
    body_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    headers = {
        "date": _rfc_1123_date(),
        "host": parsed.netloc,
        "content-type": "application/json",
        "content-length": str(len(body_bytes)),
        "x-content-sha256": base64.b64encode(hashlib.sha256(body_bytes).digest()).decode("ascii"),
    }

    key_id = f"{config_section['tenancy']}/{config_section['user']}/{config_section['fingerprint']}"
    private_key = _load_private_key(pathlib.Path(config_section["key_file"]), passphrase or config_section.get("pass_phrase"))
    headers["authorization"] = _build_signature("POST", path_query, headers, key_id, private_key)

    response = requests.post(url, data=body_bytes, headers=headers, timeout=30)
    if not response.ok:
        detail = response.text.strip()
        raise requests.HTTPError(
            f"{response.status_code} {response.reason} - {detail or 'No response body'}",
            response=response,
        )
    return response.json()

def build_vmware_alarm_message() -> str:
    """Build a message containing all VMware alarm environment variables."""
    vmware_vars = [
        "VMWARE_ALARM_NAME",
        "VMWARE_ALARM_ID",
        "VMWARE_ALARM_TARGET_NAME",
        "VMWARE_ALARM_TARGET_ID",
        "VMWARE_ALARM_OLDSTATUS",
        "VMWARE_ALARM_NEWSTATUS",
        "VMWARE_ALARM_TRIGGERINGSUMMARY",
        "VMWARE_ALARM_DECLARINGSUMMARY",
        "VMWARE_ALARM_ALARMVALUE",
        "VMWARE_ALARM_EVENTDESCRIPTION",
        "VMWARE_ALARM_EVENT_USERNAME",
        "VMWARE_ALARM_EVENT_DATACENTER",
        "VMWARE_ALARM_EVENT_COMPUTERESOURCE",
        "VMWARE_ALARM_EVENT_HOST",
        "VMWARE_ALARM_EVENT_VM",
        "VMWARE_ALARM_EVENT_NETWORK",
        "VMWARE_ALARM_EVENT_DATASTORE",
        "VMWARE_ALARM_EVENT_DVS",
    ]
    
    lines = []
    for var_name in vmware_vars:
        value = os.environ.get(var_name)
        if value:
            lines.append(f"{var_name}: {value}")
    
    return "\n".join(lines) if lines else "Dummy test message."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a message to an OCI Notifications topic via REST.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--topic-ocid", default=None, help="Target Notifications topic OCID (defaults to 'topic' from config file if not set)")
    parser.add_argument("--subject", default=None, help="Notification subject/title (defaults to VMWARE_ALARM_DECLARINGSUMMARY if not set)")
    parser.add_argument("--message", default=None, help="Message body to publish (defaults to all VMware alarm environment variables if not set)")
    parser.add_argument(
        "--message-type",
        choices=("RAW_TEXT", "JSON"),
        default="RAW_TEXT",
        help="How Notifications should treat the payload",
    )
    parser.add_argument("--config-file", default=str(DEFAULT_CONFIG_PATH), help="Path to OCI CLI-style config file (default: /home/vpxd/config)")
    parser.add_argument("--profile", default="DEFAULT", help="Profile name inside the config file")
    parser.add_argument("--region", help="Override region instead of reading it from the profile")
    parser.add_argument("--endpoint", help="Override Notifications endpoint URL")
    parser.add_argument("--passphrase", help="Override private key passphrase if encrypted")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        profile = _load_profile(pathlib.Path(args.config_file), args.profile)
        if args.region:
            profile["region"] = args.region
        
        # Get topic OCID from args or config file
        topic_id = args.topic_ocid
        if topic_id is None:
            topic_id = profile.get("topic")
            if not topic_id:
                raise ValueError("Topic OCID not specified. Provide --topic-ocid or set 'topic' in config file")
        
        # Use VMware alarm environment variables if subject/message not specified
        subject = args.subject
        if subject is None:
            subject = os.environ.get("VMWARE_ALARM_EVENTDESCRIPTION", "vCenter dummy message")
        
        message = args.message
        if message is None:
            message = build_vmware_alarm_message()
        
        # Prepend hostname prefix to message
        hostname = socket.gethostname()
        message = f"ALARM SEND FROM: {hostname}\n\n{message}"
        
        # Enforce limits: subject max 254 chars, message max 64KB
        MAX_SUBJECT_LENGTH = 254
        MAX_MESSAGE_SIZE = 64 * 1024  # 64KB in bytes
        
        if len(subject) > MAX_SUBJECT_LENGTH:
            print(f"WARNING: Subject truncated from {len(subject)} to {MAX_SUBJECT_LENGTH} characters", file=sys.stderr)
            subject = subject[:MAX_SUBJECT_LENGTH]
        
        message_bytes = message.encode("utf-8")
        original_size = len(message_bytes)
        if original_size > MAX_MESSAGE_SIZE:
            # Truncate message to fit within 64KB limit
            # Try to truncate at a reasonable boundary (newline or space)
            truncated = message_bytes[:MAX_MESSAGE_SIZE]
            # Try to find the last newline or space before the limit
            last_newline = truncated.rfind(b"\n")
            last_space = truncated.rfind(b" ")
            # Use the last newline if found within last 1KB, otherwise use last space, otherwise hard truncate
            if last_newline > MAX_MESSAGE_SIZE - 1024:
                message = truncated[:last_newline].decode("utf-8", errors="ignore")
            elif last_space > MAX_MESSAGE_SIZE - 1024:
                message = truncated[:last_space].decode("utf-8", errors="ignore")
            else:
                message = truncated.decode("utf-8", errors="ignore")
            final_size = len(message.encode("utf-8"))
            print(f"WARNING: Message truncated from {original_size} to {final_size} bytes", file=sys.stderr)
        
        result = publish_message(
            topic_id=topic_id,
            subject=subject,
            body_text=message,
            message_type=args.message_type,
            config_section=profile,
            endpoint=args.endpoint,
            passphrase=args.passphrase,
        )
    except Exception as exc:
        raise SystemExit(f"Failed to publish message: {exc}") from exc

    message_id = result.get("messageId", "<unknown>")
    print(f"Message submitted. MessageId: {message_id}")


if __name__ == "__main__":
    main()

