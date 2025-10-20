#!/usr/bin/env python3

from __future__ import annotations

import asyncio
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio

import oci
from oci.util import to_dict

load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("enhanced-oci-mcp")


class OCIManager:
    """Enhanced manager to create OCI clients using ~/.oci/config or env-based auth."""

    def __init__(self) -> None:
        self.config = self._load_config()
        self.signer = None  # for instance principals etc.

    def _load_config(self) -> Dict[str, Any]:
        # Prefer config file if present
        cfg_file = os.getenv("OCI_CONFIG_FILE", os.path.expanduser("~/.oci/config"))
        profile = os.getenv("OCI_CONFIG_PROFILE", "DEFAULT")
        if os.path.exists(cfg_file):
            log.info(f"Using OCI config file: {cfg_file} [{profile}]")
            return oci.config.from_file(cfg_file, profile_name=profile)

        # Else try explicit env vars
        env_keys = (
            "OCI_USER_OCID",
            "OCI_FINGERPRINT",
            "OCI_TENANCY_OCID",
            "OCI_REGION",
            "OCI_KEY_FILE",
        )
        if all(os.getenv(k) for k in env_keys):
            cfg = {
                "user": os.environ["OCI_USER_OCID"],
                "fingerprint": os.environ["OCI_FINGERPRINT"],
                "tenancy": os.environ["OCI_TENANCY_OCID"],
                "region": os.environ["OCI_REGION"],
                "key_file": os.environ["OCI_KEY_FILE"],
            }
            log.info("Using explicit OCI env var configuration")
            return cfg

        # Finally, try instance principals (for servers running on OCI)
        try:
            self.signer = oci.auth.signers.get_resource_principals_signer()
            region = os.getenv("OCI_REGION", "eu-frankfurt-1")
            cfg = {"region": region, "tenancy": os.getenv("OCI_TENANCY_OCID", "")}
            log.info("Using instance/resource principals signer")
            return cfg
        except Exception:
            raise RuntimeError(
                "No OCI credentials found. Run `oci setup config` or set env vars "
                "(OCI_USER_OCID, OCI_FINGERPRINT, OCI_TENANCY_OCID, OCI_REGION, OCI_KEY_FILE)."
            )

    def get_client(self, service: str):
        """Return an OCI service client bound to configured region/signer."""
        service = service.lower()
        kwargs = {}
        if self.signer:
            kwargs["signer"] = self.signer

        if service in ("identity", "iam"):
            return oci.identity.IdentityClient(self.config, **kwargs)
        if service in ("compute", "core"):
            return oci.core.ComputeClient(self.config, **kwargs)
        if service in ("network", "virtualnetwork", "vcn"):
            return oci.core.VirtualNetworkClient(self.config, **kwargs)
        if service in ("database", "db"):
            return oci.database.DatabaseClient(self.config, **kwargs)
        if service in ("object_storage", "objectstorage", "os"):
            return oci.object_storage.ObjectStorageClient(self.config, **kwargs)
        if service in ("usage", "usage_api", "cost"):
            try:
                return oci.usage_api.UsageapiClient(self.config, **kwargs)
            except Exception as e:
                raise RuntimeError(
                    "Usage API client not available; check OCI SDK version."
                ) from e

        raise ValueError(f"Unknown OCI service: {service}")


oci_manager = OCIManager()


# Utility: default compartment
def _default_compartment() -> Optional[str]:
    return os.getenv("DEFAULT_COMPARTMENT_OCID") or oci_manager.config.get("tenancy")


# Utility: safe dict conversion for OCI models/collections
def _to_clean_dict(x: Any) -> Any:
    try:
        return to_dict(x)
    except Exception:
        return json.loads(json.dumps(x, default=str))


def find_instances_by_name(
    display_name: str, compartment_ocid: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Find instances by display name across compartments."""
    try:
        result = []

        if compartment_ocid:
            compartments_to_search = [compartment_ocid]
        else:
            # Search all compartments in the tenancy
            compartments_to_search = []
            tenancy_id = oci_manager.config["tenancy"]
            compartments_to_search.append(tenancy_id)

            identity = oci_manager.get_client("identity")
            all_compartments = oci.pagination.list_call_get_all_results(
                identity.list_compartments,
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True,
                access_level="ACCESSIBLE",
            ).data

            for compartment in all_compartments:
                if compartment.lifecycle_state == "ACTIVE":
                    compartments_to_search.append(compartment.id)

        compute = oci_manager.get_client("compute")
        for compartment_id in compartments_to_search:
            try:
                for inst in oci.pagination.list_call_get_all_results(
                    compute.list_instances, compartment_id=compartment_id
                ).data:
                    if inst.display_name.lower() == display_name.lower():
                        result.append(
                            {
                                "id": inst.id,
                                "display_name": inst.display_name,
                                "lifecycle_state": inst.lifecycle_state,
                                "compartment_id": inst.compartment_id,
                            }
                        )
            except Exception as e:
                log.warning(f"Failed to search compartment {compartment_id}: {e}")
                continue

        return result
    except Exception as e:
        log.error(f"Error finding instances by name: {e}")
        return []


app = Server("enhanced-oci-mcp")


@app.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available OCI tools."""
    return [
        types.Tool(
            name="list_compute_instances",
            description="List compute instances with optional filtering",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (searches entire tenancy if omitted)"
                    },
                    "lifecycle_state": {
                        "type": "string",
                        "description": "Optional filter (e.g., RUNNING, STOPPED)"
                    }
                }
            }
        ),
        types.Tool(
            name="get_instance_details",
            description="Get detailed information about a compute instance",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "The OCID of the instance",
                    }
                },
                "required": ["instance_id"],
            },
        ),
        types.Tool(
            name="instance_action",
            description="Perform instance actions (START, STOP, RESET, SOFTRESET, SOFTSTOP)",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "Instance OCID"},
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["START", "STOP", "RESET", "SOFTRESET", "SOFTSTOP"],
                    },
                },
                "required": ["instance_id", "action"],
            },
        ),
        types.Tool(
            name="instance_action_by_name",
            description="Perform instance actions by display name",
            inputSchema={
                "type": "object",
                "properties": {
                    "display_name": {
                        "type": "string",
                        "description": "Instance display name",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["START", "STOP", "RESET", "SOFTRESET", "SOFTSTOP"],
                    },
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Optional compartment to search in",
                    },
                },
                "required": ["display_name", "action"],
            },
        ),
        types.Tool(
            name="batch_instance_action",
            description="Perform actions on multiple instances in a compartment",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID",
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to perform",
                        "enum": ["START", "STOP", "RESET", "SOFTRESET", "SOFTSTOP"],
                    },
                    "lifecycle_state_filter": {
                        "type": "string",
                        "description": "Only act on instances in this state (e.g., STOPPED)",
                    },
                },
                "required": ["compartment_ocid", "action"],
            },
        ),
        types.Tool(
            name="list_autonomous_databases",
            description="List Autonomous Databases in a compartment",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (defaults to tenancy if omitted)"
                    }
                }
            }
        ),
        types.Tool(
            name="list_storage_buckets",
            description="List Object Storage buckets",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (searches entire tenancy if omitted)"
                    }
                }
            }
        ),
        types.Tool(
            name="list_compartments",
            description="List accessible compartments in the tenancy",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="perform_security_assessment",
            description="Comprehensive security posture assessment",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (defaults to tenancy if omitted)",
                    }
                },
            },
        ),
        types.Tool(
            name="list_public_instances",
            description="Find all instances with public IP addresses",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (searches entire tenancy if omitted)",
                    }
                },
            },
        ),
        types.Tool(
            name="list_wide_open_security_rules",
            description="Find NSGs and security lists allowing 0.0.0.0/0 inbound",
            inputSchema={
                "type": "object",
                "properties": {
                    "compartment_ocid": {
                        "type": "string",
                        "description": "Compartment OCID (defaults to tenancy if omitted)",
                    }
                },
            },
        ),
        types.Tool(
            name="get_tenancy_cost_summary",
            description="Get tenancy cost summary using Usage API",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time_iso": {
                        "type": "string",
                        "description": "ISO8601 start time (defaults to 7 days ago)",
                    },
                    "end_time_iso": {
                        "type": "string",
                        "description": "ISO8601 end time (defaults to now)",
                    },
                    "granularity": {
                        "type": "string",
                        "description": "Time granularity",
                        "enum": ["DAILY", "MONTHLY"],
                        "default": "DAILY",
                    },
                },
            },
        ),
        types.Tool(
            name="get_top_services_by_cost",
            description="Get top services by cost for a time period",
            inputSchema={
                "type": "object",
                "properties": {
                    "start_time_iso": {
                        "type": "string",
                        "description": "ISO8601 start time (defaults to 30 days ago)",
                    },
                    "end_time_iso": {
                        "type": "string",
                        "description": "ISO8601 end time (defaults to now)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Number of top services to return",
                        "default": 10,
                    },
                },
            },
        ),
        types.Tool(
            name="ask_about_tenancy",
            description="Answer general questions about OCI tenancy and resources",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question about the tenancy",
                    }
                },
                "required": ["question"],
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    """Handle tool calls."""
    if arguments is None:
        arguments = {}

    try:
        if name == "list_compute_instances":
            result = await list_compute_instances(**arguments)
        # elif name == "list_resource_types":
        #     result = list_resource_types(**arguments)
        elif name == "get_instance_details":
            result = await get_instance_details(**arguments)
        elif name == "instance_action":
            result = await instance_action(**arguments)
        elif name == "instance_action_by_name":
            result = await instance_action_by_name(**arguments)
        elif name == "batch_instance_action":
            result = await batch_instance_action(**arguments)
        elif name == "list_autonomous_databases":
            result = await list_autonomous_databases(**arguments)
        elif name == "list_storage_buckets":
            result = await list_storage_buckets(**arguments)
        elif name == "list_compartments":
            result = await list_compartments(**arguments)
        elif name == "perform_security_assessment":
            result = await perform_security_assessment(**arguments)
        elif name == "list_public_instances":
            result = await list_public_instances(**arguments)
        elif name == "list_wide_open_security_rules":
            result = await list_wide_open_security_rules(**arguments)
        elif name == "get_tenancy_cost_summary":
            result = await get_tenancy_cost_summary(**arguments)
        elif name == "get_top_services_by_cost":
            result = await get_top_services_by_cost(**arguments)
        elif name == "ask_about_tenancy":
            result = await ask_about_tenancy(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

        # Format result as JSON string
        if isinstance(result, (dict, list)):
            content = json.dumps(result, indent=2, default=str)
        else:
            content = str(result)

        return [types.TextContent(type="text", text=content)]

    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        log.error(error_msg)
        return [types.TextContent(type="text", text=json.dumps({"error": error_msg}))]


# ---------- Tool Implementations ----------


async def list_compute_instances(
    compartment_ocid: Optional[str] = None, lifecycle_state: Optional[str] = None
) -> List[Dict[str, Any]]:
    """List Compute instances, searching all compartments if none specified."""
    try:
        result = []

        if compartment_ocid:
            # Search only the specified compartment
            compartments_to_search = [compartment_ocid]
        else:
            # Search all compartments in the tenancy
            compartments_to_search = []

            # Get all compartments including the root tenancy
            tenancy_id = oci_manager.config["tenancy"]
            compartments_to_search.append(tenancy_id)  # Include root tenancy

            # Get all sub-compartments using the same approach as cloned repo
            identity = oci_manager.get_client("identity")
            all_compartments = oci.pagination.list_call_get_all_results(
                identity.list_compartments,
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True,
                access_level="ACCESSIBLE",
            ).data

            for compartment in all_compartments:
                if compartment.lifecycle_state == "ACTIVE":
                    compartments_to_search.append(compartment.id)

        # Search each compartment for instances
        compute = oci_manager.get_client("compute")
        for compartment_id in compartments_to_search:
            try:
                for inst in oci.pagination.list_call_get_all_results(
                    compute.list_instances, compartment_id=compartment_id
                ).data:
                    if lifecycle_state and inst.lifecycle_state != lifecycle_state:
                        continue

                    # Get compartment name for better display
                    compartment_name = "root tenancy"
                    if compartment_id != oci_manager.config["tenancy"]:
                        try:
                            identity = oci_manager.get_client("identity")
                            comp = identity.get_compartment(compartment_id).data
                            compartment_name = comp.name
                        except:  # noqa
                            compartment_name = "unknown"

                    result.append(
                        {
                            "id": inst.id,
                            "display_name": inst.display_name,
                            "shape": inst.shape,
                            "lifecycle_state": inst.lifecycle_state,
                            "time_created": inst.time_created.isoformat()
                            if inst.time_created
                            else None,
                            "compartment_id": inst.compartment_id,
                            "compartment_name": compartment_name,
                            "availability_domain": getattr(
                                inst, "availability_domain", None
                            ),
                        }
                    )
            except Exception as e:
                log.warning(f"Failed to search compartment {compartment_id}: {e}")
                continue

        return result
    except Exception as e:
        log.error(f"Error listing compute instances: {e}")
        return [{"error": f"Failed to list compute instances: {str(e)}"}]


async def get_instance_details(instance_id: str) -> Dict[str, Any]:
    """Get detailed info for a Compute instance, including VNICs and public IPs."""
    try:
        compute = oci_manager.get_client("compute")
        vcn = oci_manager.get_client("network")

        inst = compute.get_instance(instance_id).data
        details: Dict[str, Any] = {
            "id": inst.id,
            "display_name": inst.display_name,
            "shape": inst.shape,
            "lifecycle_state": inst.lifecycle_state,
            "time_created": inst.time_created.isoformat()
            if inst.time_created
            else None,
            "metadata": inst.metadata,
            "extended_metadata": inst.extended_metadata,
        }

        # VNIC attachments -> VNICs
        attachments = oci.pagination.list_call_get_all_results(
            compute.list_vnic_attachments,
            compartment_id=inst.compartment_id,
            instance_id=inst.id,
        ).data

        vnics = []
        for att in attachments:
            vnic = vcn.get_vnic(att.vnic_id).data
            vnics.append(
                {
                    "id": vnic.id,
                    "display_name": vnic.display_name,
                    "hostname_label": vnic.hostname_label,
                    "private_ip": vnic.private_ip,
                    "public_ip": vnic.public_ip,
                    "subnet_id": vnic.subnet_id,
                    "is_primary": vnic.is_primary,
                }
            )
        details["vnics"] = vnics
        return details
    except Exception as e:
        log.error(f"Error getting instance details: {e}")
        return {"error": f"Failed to get instance details: {str(e)}"}


async def instance_action(instance_id: str, action: str) -> Dict[str, Any]:
    """Perform a safe instance action (START, STOP, RESET, SOFTRESET, SOFTSTOP)."""
    try:
        compute = oci_manager.get_client("compute")
        action = action.upper()
        valid = {"START", "STOP", "RESET", "SOFTRESET", "SOFTSTOP"}
        if action not in valid:
            return {"error": f"Invalid action '{action}'. Allowed: {sorted(valid)}"}

        resp = compute.instance_action(instance_id=instance_id, action=action)
        return {"success": True, "status": resp.status, "headers": dict(resp.headers)}
    except Exception as e:
        log.error(f"Error performing instance action: {e}")
        return {"error": f"Failed to perform instance action: {str(e)}"}


async def instance_action_by_name(
    display_name: str, action: str, compartment_ocid: Optional[str] = None
) -> Dict[str, Any]:
    """Perform instance action by display name."""
    try:
        instances = find_instances_by_name(display_name, compartment_ocid)
        if not instances:
            return {"error": f"No instances found with name '{display_name}'"}

        results = []
        for inst in instances:
            result = await instance_action(inst["id"], action)
            results.append(
                {
                    "instance_id": inst["id"],
                    "display_name": inst["display_name"],
                    "result": result,
                }
            )

        return {"action": action, "instances": results}
    except Exception as e:
        log.error(f"Error performing instance action by name: {e}")
        return {"error": f"Failed to perform instance action by name: {str(e)}"}


async def batch_instance_action(
    compartment_ocid: str, action: str, lifecycle_state_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Perform actions on multiple instances in a compartment."""
    try:
        # Get instances in the compartment
        instances = await list_compute_instances(
            compartment_ocid, lifecycle_state_filter
        )
        if (
            isinstance(instances, list)
            and len(instances) > 0
            and "error" in instances[0]
        ):
            return instances[0]

        results = []
        for inst in instances:
            if isinstance(inst, dict) and "id" in inst:
                result = await instance_action(inst["id"], action)
                results.append(
                    {
                        "instance_id": inst["id"],
                        "display_name": inst["display_name"],
                        "result": result,
                    }
                )

        return {
            "action": action,
            "compartment_ocid": compartment_ocid,
            "lifecycle_state_filter": lifecycle_state_filter,
            "processed_count": len(results),
            "results": results,
        }
    except Exception as e:
        log.error(f"Error performing batch instance action: {e}")
        return {"error": f"Failed to perform batch instance action: {str(e)}"}


async def list_autonomous_databases(
    compartment_ocid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List Autonomous Databases in a compartment (defaults to tenancy)."""
    try:
        comp = compartment_ocid or _default_compartment()
        if not comp:
            return [{"error": "No compartment OCID available"}]

        db = oci_manager.get_client("database")
        items = []
        for adb in oci.pagination.list_call_get_all_results(
            db.list_autonomous_databases, compartment_id=comp
        ).data:
            items.append(
                {
                    "id": adb.id,
                    "db_name": adb.db_name,
                    "display_name": adb.display_name,
                    "lifecycle_state": adb.lifecycle_state,
                    "db_workload": adb.db_workload,
                    "cpu_core_count": getattr(adb, "cpu_core_count", None),
                    "data_storage_size_in_tbs": getattr(
                        adb, "data_storage_size_in_tbs", None
                    ),
                    "is_auto_scaling_enabled": getattr(
                        adb, "is_auto_scaling_enabled", None
                    ),
                    "connection_strings": _to_clean_dict(
                        getattr(adb, "connection_strings", {})
                    ),
                }
            )
        return items
    except Exception as e:
        log.error(f"Error listing autonomous databases: {e}")
        return [{"error": f"Failed to list autonomous databases: {str(e)}"}]


async def list_storage_buckets(
    compartment_ocid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List Object Storage buckets in the configured region for the given compartment."""
    try:
        result = []

        if compartment_ocid and compartment_ocid not in ("null",):
            compartments_to_search = [compartment_ocid]
        else:
            # Search all compartments in the tenancy
            compartments_to_search = []
            tenancy_id = oci_manager.config["tenancy"]
            compartments_to_search.append(tenancy_id)

            identity = oci_manager.get_client("identity")
            all_compartments = oci.pagination.list_call_get_all_results(
                identity.list_compartments,
                compartment_id=tenancy_id,
                compartment_id_in_subtree=True,
                access_level="ACCESSIBLE",
            ).data

            for compartment in all_compartments:
                if compartment.lifecycle_state == "ACTIVE":
                    compartments_to_search.append(compartment.id)

        osvc = oci_manager.get_client("object_storage")
        namespace = osvc.get_namespace().data

        for compartment_id in compartments_to_search:
            try:
                buckets = oci.pagination.list_call_get_all_results(
                    osvc.list_buckets,
                    namespace_name=namespace,
                    compartment_id=compartment_id,
                ).data

                for b in buckets:
                    # Get compartment name for better display
                    compartment_name = "root tenancy"
                    if compartment_id != oci_manager.config["tenancy"]:
                        try:
                            identity = oci_manager.get_client("identity")
                            comp = identity.get_compartment(compartment_id).data
                            compartment_name = comp.name
                        except:
                            compartment_name = "unknown"

                    result.append(
                        {
                            "name": b.name,
                            "created": b.time_created.isoformat()
                            if b.time_created
                            else None,
                            "namespace": namespace,
                            "compartment_id": compartment_id,
                            "compartment_name": compartment_name,
                        }
                    )
            except Exception as e:
                log.warning(
                    f"Failed to search compartment {compartment_id} for buckets: {e}"
                )
                continue

        return result
    except Exception as e:
        log.error(f"Error listing storage buckets: {e}")
        return [{"error": f"Failed to list storage buckets: {str(e)}"}]


async def list_compartments() -> List[Dict[str, Any]]:
    """List accessible compartments in the tenancy (including subtrees)."""
    try:
        identity = oci_manager.get_client("identity")
        tenancy_id = oci_manager.config["tenancy"]
        comps = oci.pagination.list_call_get_all_results(
            identity.list_compartments,
            compartment_id=tenancy_id,
            compartment_id_in_subtree=True,
            access_level="ACCESSIBLE",
        ).data

        # Include root tenancy
        result = [
            {
                "id": tenancy_id,
                "name": "(root tenancy)",
                "lifecycle_state": "ACTIVE",
                "is_accessible": True,
            }
        ]

        # Add all sub-compartments
        for c in comps:
            result.append(
                {
                    "id": c.id,
                    "name": c.name,
                    "lifecycle_state": c.lifecycle_state,
                    "is_accessible": c.is_accessible,
                }
            )

        return result
    except Exception as e:
        log.error(f"Error listing compartments: {e}")
        return [{"error": f"Failed to list compartments: {str(e)}"}]


async def perform_security_assessment(
    compartment_ocid: Optional[str] = None,
) -> Dict[str, Any]:
    """Basic security posture checks (public IPs, wide-open rules). Read-only heuristics."""
    comp = compartment_ocid or _default_compartment()
    if not comp:
        return {"error": "No compartment OCID available"}

    compute = oci_manager.get_client("compute")
    net = oci_manager.get_client("network")

    findings: Dict[str, Any] = {
        "public_instances": [],
        "wide_open_nsg_rules": [],
        "wide_open_sec_list_rules": [],
    }

    try:
        # Instances with public IPs
        for inst in oci.pagination.list_call_get_all_results(
            compute.list_instances, compartment_id=comp
        ).data:
            vnic_atts = oci.pagination.list_call_get_all_results(
                compute.list_vnic_attachments, compartment_id=comp, instance_id=inst.id
            ).data
            for att in vnic_atts:
                vnic = net.get_vnic(att.vnic_id).data
                if vnic.public_ip:
                    findings["public_instances"].append(
                        {
                            "instance_id": inst.id,
                            "name": inst.display_name,
                            "public_ip": vnic.public_ip,
                        }
                    )

        # Security Lists allowing 0.0.0.0/0 inbound
        for vcn in oci.pagination.list_call_get_all_results(
            net.list_vcns, compartment_id=comp
        ).data:
            sec_lists = oci.pagination.list_call_get_all_results(
                net.list_security_lists, compartment_id=comp, vcn_id=vcn.id
            ).data
            for sl in sec_lists:
                for rule in sl.ingress_security_rules or []:
                    src = getattr(rule, "source", "")
                    if src == "0.0.0.0/0":
                        findings["wide_open_sec_list_rules"].append(
                            {
                                "security_list_id": sl.id,
                                "vcn": vcn.display_name,
                                "proto": rule.protocol,
                            }
                        )

            # NSGs
            nsgs = oci.pagination.list_call_get_all_results(
                net.list_network_security_groups, compartment_id=comp, vcn_id=vcn.id
            ).data
            for nsg in nsgs:
                rules = oci.pagination.list_call_get_all_results(
                    net.list_network_security_group_security_rules,
                    network_security_group_id=nsg.id,
                ).data
                for r in rules:
                    src = getattr(r, "source", "") or getattr(r, "source_type", "")
                    if (
                        getattr(r, "direction", "INGRESS") == "INGRESS"
                        and getattr(r, "source", "") == "0.0.0.0/0"
                    ):
                        findings["wide_open_nsg_rules"].append(
                            {
                                "nsg_id": nsg.id,
                                "name": nsg.display_name,
                                "proto": r.protocol,
                            }
                        )

        return findings
    except Exception as e:
        log.error(f"Error performing security assessment: {e}")
        return {"error": f"Failed to perform security assessment: {str(e)}"}


async def list_public_instances(
    compartment_ocid: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find all instances with public IP addresses."""
    try:
        assessment = await perform_security_assessment(compartment_ocid)
        if "error" in assessment:
            return [assessment]
        return assessment.get("public_instances", [])
    except Exception as e:
        log.error(f"Error listing public instances: {e}")
        return [{"error": f"Failed to list public instances: {str(e)}"}]


async def list_wide_open_security_rules(
    compartment_ocid: Optional[str] = None,
) -> Dict[str, Any]:
    """Find NSGs and security lists allowing 0.0.0.0/0 inbound."""
    try:
        assessment = await perform_security_assessment(compartment_ocid)
        if "error" in assessment:
            return assessment

        return {
            "wide_open_nsg_rules": assessment.get("wide_open_nsg_rules", []),
            "wide_open_sec_list_rules": assessment.get("wide_open_sec_list_rules", []),
        }
    except Exception as e:
        log.error(f"Error listing wide open security rules: {e}")
        return {"error": f"Failed to list wide open security rules: {str(e)}"}


async def get_tenancy_cost_summary(
    start_time_iso: Optional[str] = None,
    end_time_iso: Optional[str] = None,
    granularity: str = "DAILY",
) -> Dict[str, Any]:
    """Summarize tenancy costs using Usage API (requires permissions)."""
    try:
        usage = oci_manager.get_client("usage_api")
    except Exception as e:
        return {
            "error": f"Usage API not available; upgrade OCI SDK and permissions: {str(e)}"
        }

    try:
        if not end_time_iso:
            end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end = datetime.fromisoformat(end_time_iso.replace("Z", "")).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not start_time_iso:
            start = (end - timedelta(days=7)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            start = datetime.fromisoformat(start_time_iso.replace("Z", "")).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        tenant_id = oci_manager.config["tenancy"]
        details = oci.usage_api.models.RequestSummarizedUsagesDetails(
            tenant_id=tenant_id,
            time_usage_started=start,
            time_usage_ended=end,
            granularity=granularity,
            query_type="COST",
            group_by=["service"],
        )
        resp = usage.request_summarized_usages(
            request_summarized_usages_details=details
        )
        rows = (
            [to_dict(x) for x in resp.data.items]
            if getattr(resp.data, "items", None)
            else []
        )
        total = sum((r.get("computed_amount", 0) or 0) for r in rows)
        return {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "granularity": granularity,
            "total_computed_amount": total,
            "items": rows,
        }
    except Exception as e:
        log.error(f"Error getting cost summary: {e}")
        return {"error": f"Failed to get cost summary: {str(e)}"}


async def get_top_services_by_cost(
    start_time_iso: Optional[str] = None,
    end_time_iso: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Get top services by cost for a time period."""
    try:
        # Default to last 30 days if not specified
        if not end_time_iso:
            end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            end = datetime.fromisoformat(end_time_iso.replace("Z", "")).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        if not start_time_iso:
            start = (end - timedelta(days=30)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            start = datetime.fromisoformat(start_time_iso.replace("Z", "")).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

        cost_summary = await get_tenancy_cost_summary(
            start_time_iso=start.isoformat() + "Z",
            end_time_iso=end.isoformat() + "Z",
            granularity="DAILY",
        )

        if "error" in cost_summary:
            return cost_summary

        # Aggregate by service
        service_costs = {}
        for item in cost_summary.get("items", []):
            service = item.get("service", "Unknown")
            cost = item.get("computed_amount", 0) or 0
            if service in service_costs:
                service_costs[service] += cost
            else:
                service_costs[service] = cost

        # Sort by cost descending and take top N
        top_services = sorted(service_costs.items(), key=lambda x: x[1], reverse=True)[
            :limit
        ]

        return {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
            "total_services": len(service_costs),
            "top_services": [{"service": s, "total_cost": c} for s, c in top_services],
            "grand_total": sum(service_costs.values()),
        }
    except Exception as e:
        log.error(f"Error getting top services by cost: {e}")
        return {"error": f"Failed to get top services by cost: {str(e)}"}


# ----------- Resources -----------


@app.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources."""
    return [
        types.Resource(
            uri="oci://compartments",
            name="OCI Compartments",
            description="List of all accessible compartments in the tenancy",
            mimeType="application/json",
        )
    ]


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read resource content."""
    if uri == "oci://compartments":
        compartments = await list_compartments()
        return json.dumps(compartments, indent=2)
    else:
        raise ValueError(f"Unknown resource: {uri}")


async def ask_about_tenancy(question: str) -> Dict[str, Any]:
    """Answer general questions about OCI tenancy by routing to appropriate tools."""
    try:
        question_lower = question.lower()

        # Route question to appropriate tool based on content
        if "instance" in question_lower and "ocid1.instance" in question:
            # Extract OCID from question
            import re

            ocid_match = re.search(r"ocid1\.instance\.[^\s]+", question)
            if ocid_match:
                instance_id = ocid_match.group()
                return await get_instance_details(instance_id)

        if "instance" in question_lower and (
            "running" in question_lower or "active" in question_lower
        ):
            return await list_compute_instances(lifecycle_state="RUNNING")
        elif "instance" in question_lower and "public" in question_lower:
            return await list_public_instances()
        elif "instance" in question_lower:
            return await list_compute_instances()
        elif "compartment" in question_lower:
            return await list_compartments()
        elif "bucket" in question_lower or "storage" in question_lower:
            return await list_storage_buckets()
        elif "database" in question_lower or "adb" in question_lower:
            return await list_autonomous_databases()
        elif "security" in question_lower or "assessment" in question_lower:
            return await perform_security_assessment()
        elif (
            "cost" in question_lower
            or "spend" in question_lower
            or "billing" in question_lower
        ):
            return await get_tenancy_cost_summary()
        else:
            # General tenancy overview
            result = {
                "message": f"Question: {question}",
                "available_actions": [
                    "List compute instances",
                    "List compartments",
                    "List storage buckets",
                    "List autonomous databases",
                    "Perform security assessment",
                    "Get cost summary",
                    "Find public instances",
                    "Get instance details (provide OCID)",
                ],
                "suggestion": "Try asking about specific resources like 'show me running instances' or 'what compartments do I have?'",
            }
            return result

    except Exception as e:
        log.error(f"Error in ask_about_tenancy: {e}")
        return {"error": f"Error processing question: {str(e)}"}


# ----------- Prompts -----------


@app.list_prompts()
async def handle_list_prompts() -> list[types.Prompt]:
    """List available prompts."""
    return [
        types.Prompt(
            name="oci_analysis_prompt",
            description="A helper prompt to analyze OCI state returned by the tools",
        )
    ]


@app.get_prompt()
async def handle_get_prompt(
    name: str, arguments: dict[str, str] | None = None
) -> types.GetPromptResult:
    """Get prompt content."""
    if name == "oci_analysis_prompt":
        return types.GetPromptResult(
            description="Analyze OCI infrastructure state",
            messages=[
                types.PromptMessage(
                    role="user",
                    content=types.TextContent(
                        type="text",
                        text=(
                            "You are an expert Oracle Cloud architect. Given the JSON outputs from tools like "
                            "`list_compute_instances`, `perform_security_assessment`, and `get_tenancy_cost_summary`, "
                            "produce a concise assessment covering security, cost, and reliability. "
                            "Highlight risky public exposure, suggest least-privilege hardening, recommend cost optimizations "
                            "(stop idle instances, enable ADB auto-scaling), and note any missing monitoring/alerts."
                        ),
                    ),
                )
            ],
        )
    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="enhanced-oci-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
