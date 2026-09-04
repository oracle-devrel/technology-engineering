#!/usr/bin/env python3
"""
CRR Warm Standby API CLI

This script helps in orchestration of the PostgreSQL DB System CRR Warm Standby APIs

Auth modes:
  - resource_principal (default)
  - config (OCI API key config file/profile)
"""

from __future__ import annotations

import argparse
import json
import os
import time
import sys
import uuid
from dataclasses import dataclass
from typing import Any

import oci
import requests


API_VERSION_PATH = "/20220915"
ASYNC_ACTIONS = {
    "change-role-to-standalone",
    "change-role-to-replica",
    "switchover",
}
SUCCESS_STATES = {"SUCCEEDED", "SUCCESS"}
FAILED_STATES = {"FAILED", "CANCELED", "CANCELLED", "ERROR"}


@dataclass(frozen=True)
class ActionSpec:
    method: str
    path_template: str
    requires_db_system_id: bool = False
    requires_body: bool = False


ACTIONS: dict[str, ActionSpec] = {
    "list-replicas": ActionSpec(
        method="GET",
        path_template="/dbSystems/{dbSystemId}/replicas",
        requires_db_system_id=True,
    ),
    "change-role-to-standalone": ActionSpec(
        method="POST",
        path_template="/dbSystems/{dbSystemId}/actions/changeRoleToStandalone",
        requires_db_system_id=True,
        requires_body=True,
    ),
    "change-role-to-replica": ActionSpec(
        method="POST",
        path_template="/dbSystems/{dbSystemId}/actions/changeRoleToReplica",
        requires_db_system_id=True,
        requires_body=True,
    ),
    "switchover": ActionSpec(
        method="POST",
        path_template="/dbSystems/{dbSystemId}/actions/switchover",
        requires_db_system_id=True,
        requires_body=True,
    ),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Execute CRR Warm Standby APIs with OCI request signing.",
    )

    parser.add_argument("--action", required=True, choices=sorted(ACTIONS.keys()))

    # Endpoint controls
    parser.add_argument(
        "--endpoint",
        help=(
            "Service endpoint root (example: https://postgresql.us-phoenix-1.oci.oraclecloud.com). "
            "If omitted, built from --region."
        ),
    )
    parser.add_argument(
        "--region",
        help="OCI region used to construct endpoint if --endpoint is omitted.",
    )

    # Common request params
    parser.add_argument("--db-system-id", help="Database system OCID for path parameter.")
    parser.add_argument("--body-file", help="Path to JSON file for request body.")
    parser.add_argument("--if-match", help="Optional if-match header.")
    parser.add_argument("--opc-request-id", help="Optional opc-request-id. Auto-generated if omitted.")
    parser.add_argument("--opc-retry-token", help="Optional opc-retry-token header.")

    # list-replicas query params
    parser.add_argument("--limit", type=int, help="Optional pagination limit for list-replicas.")
    parser.add_argument("--page", help="Optional page token for list-replicas.")

    # Auth controls
    parser.add_argument(
        "--auth-mode",
        choices=["resource_principal", "config"],
        default=None,
        help="Authentication mode. Overrides body-file settings if provided.",
    )
    parser.add_argument(
        "--config-file",
        default=None,
        help="OCI config file path (used when --auth-mode config).",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="OCI config profile (used when --auth-mode config).",
    )

    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (not recommended).",
    )

    parser.add_argument(
        "--wait",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Wait for async work-request completion (default: true).",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=None,
        help="Polling interval in seconds while waiting for work request completion.",
    )
    parser.add_argument(
        "--max-wait-seconds",
        type=int,
        default=None,
        help="Maximum wait time in seconds for async operations.",
    )
    parser.add_argument(
        "--work-request-path-template",
        default="/workRequests/{workRequestId}",
        help="Work request path template relative to API version path.",
    )

    return parser.parse_args()


def validate_args(
    action: str,
    endpoint: str | None,
    region: str | None,
    db_system_id: str | None,
    body_payload: dict[str, Any] | None,
    poll_interval_seconds: int,
    max_wait_seconds: int,
) -> None:
    action_spec = ACTIONS[action]

    if not endpoint and not region:
        raise ValueError("Either --endpoint or --region is required.")

    if action_spec.requires_db_system_id and not db_system_id:
        raise ValueError(f"--db-system-id is required for action '{action}'.")

    if action_spec.requires_body and body_payload is None:
        raise ValueError(
            f"Action '{action}' requires request payload. Provide it in --body-file as payload or top-level JSON body."
        )

    if action == "change-role-to-replica":
        if not isinstance(body_payload, dict) or not body_payload.get("primaryDbSystemId"):
            raise ValueError(
                "Action 'change-role-to-replica' requires payload.primaryDbSystemId in --body-file."
            )

    if poll_interval_seconds < 1:
        raise ValueError("--poll-interval-seconds must be >= 1")

    if max_wait_seconds < 1:
        raise ValueError("--max-wait-seconds must be >= 1")


def get_signer(auth_mode: str, config_file: str, profile: str) -> Any:
    if auth_mode == "resource_principal":
        if "OCI_RESOURCE_PRINCIPAL_VERSION" not in os.environ:
            raise RuntimeError(
                "Resource Principal auth requested, but OCI_RESOURCE_PRINCIPAL_VERSION is not defined. "
                "Use --auth-mode config for local runs."
            )
        return oci.auth.signers.get_resource_principals_signer()

    config = oci.config.from_file(file_location=config_file, profile_name=profile)
    return oci.signer.Signer(
        tenancy=config["tenancy"],
        user=config["user"],
        fingerprint=config["fingerprint"],
        private_key_file_location=config["key_file"],
        pass_phrase=config.get("pass_phrase"),
    )


def build_endpoint(endpoint: str | None, region: str | None) -> str:
    if endpoint:
        return endpoint.rstrip("/")
    return f"https://postgresql.{region}.oci.oraclecloud.com"


def load_body(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_body_document(body_document: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not body_document:
        return {}, None

    settings = body_document.get("settings")
    payload = body_document.get("payload")

    if isinstance(settings, dict):
        # Combined format: {"settings": {...}, "payload": {...}}
        if payload is None:
            return settings, None
        if not isinstance(payload, dict):
            raise ValueError("'payload' in body-file must be a JSON object.")
        return settings, payload

    # Backward compatibility: file is the direct request payload.
    return {}, body_document


def pick_value(cli_value: Any, settings: dict[str, Any], *setting_keys: str, default: Any = None) -> Any:
    if cli_value is not None:
        return cli_value
    for key in setting_keys:
        if key in settings and settings[key] is not None:
            return settings[key]
    return default


def get_work_request_state(payload: dict[str, Any]) -> str | None:
    # Handle common naming variants used by OCI services.
    state = payload.get("status") or payload.get("lifecycleState") or payload.get("state")
    if isinstance(state, str):
        return state.upper()
    return None


def poll_work_request(
    endpoint: str,
    signer: Any,
    work_request_id: str,
    opc_request_id: str,
    poll_interval_seconds: int,
    max_wait_seconds: int,
    work_request_path_template: str,
    verify_tls: bool,
) -> tuple[bool, dict[str, Any], int, float]:
    poll_path = work_request_path_template.format(workRequestId=work_request_id)
    poll_url = f"{endpoint}{API_VERSION_PATH}{poll_path}"
    start = time.time()
    last_payload: dict[str, Any] = {}
    poll_count = 0

    while True:
        poll_count += 1
        resp = requests.get(
            poll_url,
            headers={
                "accept": "application/json",
                "opc-request-id": opc_request_id,
            },
            auth=signer,
            verify=verify_tls,
            timeout=120,
        )

        try:
            payload = resp.json()
        except ValueError:
            payload = {"raw": resp.text}

        last_payload = {
            "status_code": resp.status_code,
            "headers": {
                "opc-request-id": resp.headers.get("opc-request-id"),
                "etag": resp.headers.get("etag"),
            },
            "body": payload,
            "poll_url": poll_url,
        }

        if not resp.ok:
            elapsed = int(time.time() - start)
            print(
                f"[poll] elapsed={elapsed}s work_request_id={work_request_id} "
                f"http_status={resp.status_code} state=UNKNOWN result=HTTP_ERROR",
                file=sys.stderr,
            )
            return False, last_payload, poll_count, (time.time() - start)

        state = get_work_request_state(payload)
        elapsed = int(time.time() - start)
        print(
            f"[poll] elapsed={elapsed}s work_request_id={work_request_id} "
            f"http_status={resp.status_code} state={state or 'UNKNOWN'}",
            file=sys.stderr,
        )

        if state in SUCCESS_STATES:
            print(
                f"[poll] completed work_request_id={work_request_id} state={state} result=SUCCESS",
                file=sys.stderr,
            )
            return True, last_payload, poll_count, (time.time() - start)
        if state in FAILED_STATES:
            print(
                f"[poll] completed work_request_id={work_request_id} state={state} result=FAILED",
                file=sys.stderr,
            )
            return False, last_payload, poll_count, (time.time() - start)

        if (time.time() - start) >= max_wait_seconds:
            last_payload["timeout"] = {
                "max_wait_seconds": max_wait_seconds,
                "last_state": state,
            }
            print(
                f"[poll] completed work_request_id={work_request_id} state={state or 'UNKNOWN'} result=TIMEOUT",
                file=sys.stderr,
            )
            return False, last_payload, poll_count, (time.time() - start)

        time.sleep(poll_interval_seconds)


def main() -> int:
    try:
        op_start = time.time()
        args = parse_args()
        body_document = load_body(args.body_file)
        settings, body_payload = parse_body_document(body_document)

        region = pick_value(args.region, settings, "region")
        endpoint_arg = pick_value(args.endpoint, settings, "endpoint")
        db_system_id = pick_value(args.db_system_id, settings, "db_system_id", "dbSystemId")

        auth_mode = pick_value(args.auth_mode, settings, "auth_mode", "authMode", default="resource_principal")
        config_file = pick_value(
            args.config_file,
            settings,
            "oci_config_file",
            "config_file",
            "ociConfigFile",
            default=oci.config.DEFAULT_LOCATION,
        )
        profile = pick_value(
            args.profile,
            settings,
            "oci_profile",
            "profile",
            "ociProfile",
            default=oci.config.DEFAULT_PROFILE,
        )

        wait_for_async = bool(pick_value(args.wait, settings, "wait", default=True))
        poll_interval_seconds = int(
            pick_value(args.poll_interval_seconds, settings, "poll_interval_seconds", "pollIntervalSeconds", default=10)
        )
        max_wait_seconds = int(
            pick_value(args.max_wait_seconds, settings, "max_wait_seconds", "maxWaitSeconds", default=3600)
        )

        validate_args(
            action=args.action,
            endpoint=endpoint_arg,
            region=region,
            db_system_id=db_system_id,
            body_payload=body_payload,
            poll_interval_seconds=poll_interval_seconds,
            max_wait_seconds=max_wait_seconds,
        )

        action_spec = ACTIONS[args.action]
        signer = get_signer(auth_mode=auth_mode, config_file=config_file, profile=profile)
        endpoint = build_endpoint(endpoint_arg, region)

        request_path = action_spec.path_template.format(dbSystemId=db_system_id)
        url = f"{endpoint}{API_VERSION_PATH}{request_path}"

        headers: dict[str, str] = {
            "opc-request-id": args.opc_request_id or str(uuid.uuid4()),
            "accept": "application/json",
        }
        if args.if_match:
            headers["if-match"] = args.if_match
        if args.opc_retry_token:
            headers["opc-retry-token"] = args.opc_retry_token

        params: dict[str, Any] = {}
        if args.action == "list-replicas":
            if args.limit is not None:
                params["limit"] = args.limit
            if args.page:
                params["page"] = args.page

        if body_payload is not None:
            headers["content-type"] = "application/json"

        initial_call_start = time.time()
        response = requests.request(
            method=action_spec.method,
            url=url,
            headers=headers,
            params=params or None,
            json=body_payload,
            auth=signer,
            verify=not args.insecure,
            timeout=120,
        )
        initial_call_duration_seconds = time.time() - initial_call_start

        output = {
            "request": {
                "action": args.action,
                "method": action_spec.method,
                "url": url,
                "query": params,
                "opc-request-id": headers["opc-request-id"],
            },
            "response": {
                "status_code": response.status_code,
                "timing": {
                    "initial_call_duration_seconds": round(initial_call_duration_seconds, 3),
                },
                "headers": {
                    "opc-request-id": response.headers.get("opc-request-id"),
                    "opc-work-request-id": response.headers.get("opc-work-request-id"),
                    "etag": response.headers.get("etag"),
                    "opc-next-page": response.headers.get("opc-next-page"),
                },
            },
        }

        try:
            output["response"]["body"] = response.json()
        except ValueError:
            output["response"]["body"] = response.text

        print(json.dumps(output, indent=2, sort_keys=False))

        if not response.ok:
            return 1

        if wait_for_async and args.action in ASYNC_ACTIONS:
            work_request_id = response.headers.get("opc-work-request-id")
            if not work_request_id:
                print(
                    "ERROR: Async operation did not return opc-work-request-id; cannot poll for completion.",
                    file=sys.stderr,
                )
                return 1

            success, work_request_result, poll_count, polling_duration_seconds = poll_work_request(
                endpoint=endpoint,
                signer=signer,
                work_request_id=work_request_id,
                opc_request_id=headers["opc-request-id"],
                poll_interval_seconds=poll_interval_seconds,
                max_wait_seconds=max_wait_seconds,
                work_request_path_template=args.work_request_path_template,
                verify_tls=not args.insecure,
            )

            total_operation_duration_seconds = time.time() - op_start
            average_poll_interval_seconds = (
                polling_duration_seconds / (poll_count - 1) if poll_count > 1 else 0.0
            )

            final_output = {
                "initial_request": output["request"],
                "initial_response": output["response"],
                "timing": {
                    "operation": args.action,
                    "initial_call_duration_seconds": round(initial_call_duration_seconds, 3),
                    "polling_duration_seconds": round(polling_duration_seconds, 3),
                    "total_operation_duration_seconds": round(total_operation_duration_seconds, 3),
                    "poll_count": poll_count,
                    "average_poll_interval_seconds": round(average_poll_interval_seconds, 3),
                },
                "work_request": {
                    "id": work_request_id,
                    "completed_successfully": success,
                    "final_poll_result": work_request_result,
                },
            }
            print(json.dumps(final_output, indent=2, sort_keys=False))
            print(
                f"[summary] action={args.action} total={total_operation_duration_seconds:.3f}s "
                f"initial_call={initial_call_duration_seconds:.3f}s polling={polling_duration_seconds:.3f}s "
                f"poll_count={poll_count}",
                file=sys.stderr,
            )
            return 0 if success else 1

        return 0

    except Exception as exc:  # pylint: disable=broad-except
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
