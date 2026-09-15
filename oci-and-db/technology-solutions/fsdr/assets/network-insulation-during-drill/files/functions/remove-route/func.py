# -----------------------------------------------------------------------------
# Copyright (c) 2026 Oracle and/or its affiliates.
#
# Licensed under the Universal Permissive License v 1.0 as shown at
# https://oss.oracle.com/licenses/upl/
#
# You may use, copy, modify, and distribute this software and its documentation
# under the terms of the UPL. This software is provided "AS IS" without warranty
# of any kind.
#
# Oracle does not provide support for this script; community support only.
# This software is provided as it is and need to be considered an example
# of a possible implementation rather than for general use. 
#
# Script provided by: Cristiano Ghirardi, Oracle employee
# -----------------------------------------------------------------------------

"""OCI Function to remove a specific route rule from a given route table.

The function expects a JSON payload with the following keys:
    - ``rt_id``  : OCID of the route table to search.
    - ``cidr``   : Destination CIDR block of the route rule to remove.

It uses the OCI Python SDK with **resource-principal** authentication to:
1. Retrieve the specified route table.
2. Locate the route rule whose ``destination`` matches the provided CIDR.
3. Update the route table by removing that rule.

The function returns a JSON response indicating success, not-found, or any error
information.
"""

import io
import json
import logging
import ipaddress

from fdk import response
import oci


def _remove_route_rule(rt_id: str, cidr: str) -> dict:
    """Remove route rule(s) matching the given CIDR block from a specific route table."""
    signer = oci.auth.signers.get_resource_principals_signer()
    vcn_client = oci.core.VirtualNetworkClient(config={}, signer=signer)

    route_table = vcn_client.get_route_table(rt_id).data
    route_rules = list(route_table.route_rules) if route_table.route_rules else []

    matching_rules = [
        r
        for r in route_rules
        if getattr(r, "destination", None) == cidr and getattr(r, "destination_type", "CIDR_BLOCK") == "CIDR_BLOCK"
    ]
    if not matching_rules:
        return {
            "status": "not_found",
            "message": "No route rule found for the provided CIDR block in the specified route table.",
        }

    new_rules = [
        r
        for r in route_rules
        if not (
            getattr(r, "destination", None) == cidr
            and getattr(r, "destination_type", "CIDR_BLOCK") == "CIDR_BLOCK"
        )
    ]
    update_details = oci.core.models.UpdateRouteTableDetails(route_rules=new_rules)
    vcn_client.update_route_table(rt_id, update_details)

    return {
        "status": "removed",
        "route_table_id": rt_id,
        "removed_rules": len(matching_rules),
    }


def handler(ctx, data: io.BytesIO = None):
    """Function entry point.

    Expects a JSON payload with ``rt_id`` and ``cidr``.
    """
    logger = logging.getLogger()

    try:
        payload = json.loads(data.getvalue()) if data else {}
        rt_id = payload["rt_id"].strip()
        cidr = payload["cidr"].strip()

        if not rt_id or not cidr:
            raise ValueError("'rt_id' and 'cidr' must be non-empty strings")

        ipaddress.ip_network(cidr, strict=False)
    except Exception as ex:
        logger.error("Invalid input payload: %s", ex)
        return response.Response(
            ctx,
            response_data=json.dumps({"error": "Invalid input payload", "details": str(ex)}),
            headers={"Content-Type": "application/json"},
            status_code=400,
        )

    try:
        result = _remove_route_rule(rt_id, cidr)
        status_code = 200 if result.get("status") == "removed" else 404
        return response.Response(
            ctx,
            response_data=json.dumps(result),
            headers={"Content-Type": "application/json"},
            status_code=status_code,
        )
    except oci.exceptions.ServiceError as ex:
        logger.error("OCI service error while removing route rule: %s", ex)
        mapped_status = 404 if ex.status == 404 else 500
        return response.Response(
            ctx,
            response_data=json.dumps(
                {
                    "error": "OCI service error",
                    "status": ex.status,
                    "code": ex.code,
                    "message": ex.message,
                }
            ),
            headers={"Content-Type": "application/json"},
            status_code=mapped_status,
        )
    except Exception as ex:
        logger.exception("Unexpected error while removing route rule")
        return response.Response(
            ctx,
            response_data=json.dumps({"error": "Internal server error", "details": str(ex)}),
            headers={"Content-Type": "application/json"},
            status_code=500,
        )
