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


"""OCI Function to add a route rule to a specific route table.

The function expects a JSON payload with the following keys:
    - ``rt_id``  : OCID of the route table where the rule will be added.
    - ``gw_id`` : OCID of the DRG to set as gateway in the route rule.
    - ``cidr``   : Destination CIDR block for the new route rule.

The function uses **resource-principal** authentication, which is appropriate for
functions deployed in OCI Functions.
"""

import io
import json
import logging
import ipaddress

from fdk import response
import oci


def _add_route_rule(rt_id: str, gw_id: str, cidr: str) -> dict:
    """Add a route rule pointing to the provided DRG."""
    signer = oci.auth.signers.get_resource_principals_signer()
    vcn_client = oci.core.VirtualNetworkClient(config={}, signer=signer)

    route_table = vcn_client.get_route_table(rt_id).data
    existing_rules = list(route_table.route_rules) if route_table.route_rules else []

    duplicate_rule = any(
        getattr(rule, "destination", None) == cidr
        and getattr(rule, "network_entity_id", None) == gw_id
        and getattr(rule, "destination_type", "CIDR_BLOCK") == "CIDR_BLOCK"
        for rule in existing_rules
    )
    if duplicate_rule:
        return {
            "status": "already_exists",
            "message": "A matching CIDR route rule for the provided gateway already exists.",
            "route_table_id": rt_id,
            "cidr": cidr,
            "gw_id": gw_id,
        }

    new_rule = oci.core.models.RouteRule(
        network_entity_id=gw_id,
        destination=cidr,
        destination_type="CIDR_BLOCK",
    )

    updated_rules = existing_rules + [new_rule]
    update_details = oci.core.models.UpdateRouteTableDetails(route_rules=updated_rules)
    vcn_client.update_route_table(rt_id, update_details)

    return {
        "status": "added",
        "route_table_id": rt_id,
        "cidr": cidr,
        "gw_id": gw_id,
    }


def handler(ctx, data: io.BytesIO = None):
    """Function entry point.

    Expects a JSON payload with ``rt_id``, ``gw_id`` and ``cidr``.
    """
    logger = logging.getLogger()

    try:
        payload = json.loads(data.getvalue()) if data else {}
        rt_id = payload["rt_id"].strip()
        gw_id = payload["gw_id"].strip()
        cidr = payload["cidr"].strip()

        if not rt_id or not gw_id or not cidr:
            raise ValueError("'rt_id', 'gw_id' and 'cidr' must be non-empty strings")

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
        result = _add_route_rule(rt_id, gw_id, cidr)
        status_code = 200 if result.get("status") in {"added", "already_exists"} else 500
        return response.Response(
            ctx,
            response_data=json.dumps(result),
            headers={"Content-Type": "application/json"},
            status_code=status_code,
        )
    except oci.exceptions.ServiceError as ex:
        logger.error("OCI service error while adding route rule: %s", ex)
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
        logger.exception("Unexpected error while adding route rule")
        return response.Response(
            ctx,
            response_data=json.dumps({"error": "Internal server error", "details": str(ex)}),
            headers={"Content-Type": "application/json"},
            status_code=500,
        )
