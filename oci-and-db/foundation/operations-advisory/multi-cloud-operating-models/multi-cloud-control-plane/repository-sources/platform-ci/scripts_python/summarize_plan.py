#!/usr/bin/env python3
"""Render reviewable Terraform resource changes without publishing plan values."""

import argparse
from collections import Counter
import json
import re
import sys


ACTIONS = {
    ("create",), ("read",), ("update",), ("delete",), ("no-op",),
    ("forget",), ("delete", "create"), ("create", "delete"),
}
LABELS = {
    "oci_core_network_security_group": "OCI network security group",
    "oci_core_network_security_group_security_rule": "OCI network security rule",
    "oci_database_autonomous_database": "OCI Autonomous Database",
    "oci_core_instance": "OCI Compute instance",
    "azapi_resource": "Azure API resource",
    "azurerm_linux_virtual_machine": "Azure Linux virtual machine",
    "google_compute_instance": "Google Compute instance",
    "time_sleep": "Terraform wait helper",
    "local_file": "local Terraform output file",
}
COUNTERS = ("add", "change", "destroy", "replace")


def has_unknown(value):
    if isinstance(value, dict):
        return any(has_unknown(item) for item in value.values())
    if isinstance(value, list):
        return any(has_unknown(item) for item in value)
    return value is True


def attribute_name(name):
    # Nested map keys are user-controlled and are never printed. Only resource
    # schema-level names are useful here; all values remain private regardless
    # of the provider's sensitive markings (notably Vault data sources).
    if isinstance(name, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,95}", name):
        return name
    return "[attribute name omitted]"


def attribute_maps(change):
    before, after = change.get("before"), change.get("after")
    before = {} if before is None else before
    after = {} if after is None else after
    unknown = change.get("after_unknown")
    unknown = {} if unknown is None or unknown is False else unknown
    if not all(isinstance(value, dict) for value in (before, after, unknown)):
        raise ValueError("Invalid resource attribute maps")
    return before, after, unknown


def same_value(before, after, key):
    if (key in before) != (key in after):
        return False
    # Python equates True and 1, unlike JSON and Terraform.
    return json.dumps(before.get(key), sort_keys=True) == json.dumps(after.get(key), sort_keys=True)


def changed_attributes(change):
    before, after, unknown = attribute_maps(change)
    return sorted({attribute_name(key) for key in set(before) | set(after) | set(unknown)
                   if not same_value(before, after, key) or has_unknown(unknown.get(key))})


def attribute_details(change, actions):
    before, after, unknown = attribute_maps(change)
    attributes = []
    for key in sorted(set(before) | set(after) | set(unknown)):
        if actions == ("update",) and same_value(before, after, key) and not has_unknown(unknown.get(key)):
            continue
        sensitive = any(
            has_unknown(flags.get(key)) if isinstance(flags, dict) else has_unknown(flags)
            for flags in (change.get("before_sensitive"), change.get("after_sensitive"))
        )
        if sensitive:
            marker = "sensitive value withheld"
        elif has_unknown(unknown.get(key)):
            attributes.append(f"  {attribute_name(key)}: (known after apply)")
            continue
        else:
            marker = "value withheld"
        if actions == ("create",) or (before.get(key) is None and after.get(key) is not None):
            operation = "set"
        elif (actions in {("delete",), ("forget",)} or (key in before and key not in after)
              or (before.get(key) is not None and after.get(key) is None)):
            operation = "remove"
        elif same_value(before, after, key):
            operation = "retain"
        else:
            operation = "change"
        attributes.append(f"  {attribute_name(key)}: {operation} ({marker})")
    paths = change.get("replace_paths") or []
    if not isinstance(paths, list):
        raise ValueError("Invalid replacement paths")
    replacement_attributes = sorted({attribute_name(path[0]) for path in paths if isinstance(path, list) and path})
    if replacement_attributes:
        attributes.append("  replacement attributes: " + ", ".join(replacement_attributes))
    return attributes


def format_counts(counts):
    return (f"{counts['add']} to add, {counts['change']} to change, "
            f"{counts['destroy']} to destroy; {counts['replace']} replacement(s).")


def render_review(plan):
    if (not isinstance(plan, dict)
            or not str(plan.get("format_version", "")).startswith("1.")
            or plan.get("errored") is True or plan.get("complete") is False
            or plan.get("deferred_changes")
            or not isinstance(plan.get("resource_changes", []), list)):
        raise ValueError("Invalid or incomplete plan")
    totals = Counter({key: 0 for key in COUNTERS})
    cloud = totals.copy()
    supporting = totals.copy()
    groups = Counter()
    details = []
    changed_types = set()
    forgotten = 0
    for resource in plan.get("resource_changes", []):
        if not isinstance(resource, dict):
            raise ValueError("Invalid resource")
        if resource.get("mode") == "data":
            continue
        if resource.get("mode") != "managed":
            raise ValueError("Invalid resource mode")
        change = resource["change"]
        actions = tuple(change["actions"])
        if actions not in ACTIONS or change.get("importing"):
            raise ValueError("Unsupported resource action")
        if actions == ("no-op",):
            continue
        kind = resource.get("type", "resource")
        if not isinstance(kind, str) or not re.fullmatch(r"[a-z][a-z0-9_]{0,127}", kind):
            raise ValueError("Invalid resource type")
        is_cloud = kind.startswith(("oci_", "azapi_", "azurerm_", "google_"))
        counts = cloud if is_cloud else supporting
        for key, present in (("add", "create" in actions), ("change", "update" in actions),
                             ("destroy", "delete" in actions), ("replace", "create" in actions and "delete" in actions)):
            totals[key] += int(present)
            counts[key] += int(present)
        operation = "Replace" if "create" in actions and "delete" in actions else {
            "create": "Create", "update": "Update", "delete": "Delete",
            "read": "Read", "forget": "Forget",
        }[actions[0]]
        label = LABELS.get(kind, ("cloud resource" if is_cloud else "Terraform resource") + f" ({kind})")
        groups[operation, label] += 1
        forgotten += int(actions == ("forget",))
        changed_types.add(kind)
        address = resource["address"]
        if not isinstance(address, str) or len(address) > 512 or not re.fullmatch(r'[A-Za-z0-9_.\[\]"/-]+', address):
            address = "[resource address omitted]"
        details.append(f"{', '.join(actions)}: {address}")
        details.extend(attribute_details(change, actions))
        details.append("")
    summary = ["Plan: " + format_counts(totals),
               "Cloud resources: " + format_counts(cloud),
               "Terraform supporting resources: " + format_counts(supporting), ""]
    for (operation, label), count in sorted(groups.items()):
        summary.append(f"- {operation} {count} {label}{'s' if count != 1 else ''}.")
    if groups:
        summary.append("")
    else:
        summary.append("No managed resource changes are planned.")
    if ("oci_core_network_security_group" in changed_types
            and changed_types <= {"oci_core_network_security_group", "time_sleep", "local_file"}):
        summary.append("No separate OCI NSG rule resource actions are listed.")
    if totals["destroy"] or totals["replace"]:
        summary.append("Review deletions and replacements before merge; replacement adds and destroys overlap the totals.")
    if forgotten:
        summary.append(f"Review required: {forgotten} resource(s) will be removed from Terraform state; this action does not delete them in the cloud.")
    detail = "\n".join(details).strip() if details else "No managed resource changes."
    detail += "\nValues, nested map keys, data-source contents and Terraform output values are withheld. Review the manifest diff for declared settings."
    report = {"summary": "\n\n".join(summary[:3]) + "\n\n" + "\n".join(summary[4:]), "detail": detail}
    if len(report["summary"]) + len(report["detail"]) > 800000:
        raise ValueError("Safe review exceeds the publication size limit")
    return report


# Only fixed labels reach public output; provider messages can contain credentials.
DIAGNOSTIC_HINTS = {
    "authentication": ("invalidauthenticationtoken", "notauthenticated", "invalid_client", "authentication failed", "expiredtoken"),
    "authorization": ("notauthorizedornotfound", "authorizationfailed", "authorizationpermissionmismatch", "permissiondenied", "permission denied", "accessdenied", "access denied"),
    "quota": ("quotaexceeded", "quota exceeded", "limitexceeded", "limit exceeded", "service limit"),
    "configuration": ("unsupported argument", "invalid value for variable", "missing required argument", "invalid reference", "invalidparameter"),
    "connectivity": ("connection timed out", "connection refused", "no such host", "i/o timeout", "tls handshake timeout"),
}


def diagnostic_summary(log: str, stage: str) -> str:
    lowered = log.casefold()
    categories = [name for name, hints in DIAGNOSTIC_HINTS.items() if any(hint in lowered for hint in hints)]
    category = ", ".join(categories) if categories else "unclassified"
    return f"Terraform {stage} failed. Possible cause category: {category}. Raw diagnostics are withheld because they may contain secrets."


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--diagnostics", choices=("plan", "apply"), help="Classify a private log without publishing its contents")
    args = parser.parse_args()
    if args.diagnostics:
        print(diagnostic_summary(sys.stdin.read(), args.diagnostics))
        return 0
    try:
        review = render_review(json.load(sys.stdin))
        # Build the entire public report before printing: invalid later entries
        # must not leave a partial report that could be mistaken for success.
        print(json.dumps(review) if args.format == "json" else review["summary"] + "\n\n" + review["detail"])
    except (ValueError, TypeError, KeyError, AttributeError):
        print("Cannot produce a safe Terraform review.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
