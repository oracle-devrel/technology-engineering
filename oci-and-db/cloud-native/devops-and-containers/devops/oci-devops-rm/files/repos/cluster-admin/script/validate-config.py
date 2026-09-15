#!/usr/bin/env python3
import argparse
from collections import defaultdict
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
VERSION = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]*$")


def fail(message):
    raise ValueError(message)


def load_yaml(path):
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)


def validate_label(value, field):
    if not isinstance(value, str) or len(value) > 63 or not DNS_LABEL.fullmatch(value):
        fail(f"{field} must be a Kubernetes DNS label of at most 63 characters: {value!r}")


def changed_files(repo, commit, mode):
    if mode == "all":
        return [str(path.relative_to(repo)) for path in repo.rglob("*") if path.is_file()]
    try:
        parent_count = subprocess.check_output(
            ["git", "-C", str(repo), "rev-list", "--parents", "-n", "1", commit], text=True
        ).strip().split()
        if len(parent_count) < 2:
            return [str(path.relative_to(repo)) for path in repo.rglob("*") if path.is_file()]
        output = subprocess.check_output(
            ["git", "-C", str(repo), "diff", "--name-only", f"{commit}^", commit], text=True
        )
        return [line for line in output.splitlines() if line]
    except subprocess.CalledProcessError as exc:
        fail(f"Unable to determine files changed by commit {commit}: {exc}")


def validate(repo, commit, mode):
    clusters = {"noprod", "prod"}

    catalog = load_yaml(repo / "catalog/tools.yaml")
    tools = catalog.get("tools") if isinstance(catalog, dict) else None
    if not isinstance(tools, dict):
        fail("catalog/tools.yaml must contain a tools mapping")

    for tool_name, chart in tools.items():
        validate_label(tool_name, f"catalog tool {tool_name}")
        if not isinstance(chart, dict):
            fail(f"Catalog entry {tool_name} must be an object")
        if not isinstance(chart.get("chart"), str) or not chart["chart"].strip():
            fail(f"Catalog tool {tool_name} must define an upstream chart name")
        if not isinstance(chart.get("repository"), str) or not chart["repository"].startswith(("https://", "oci://")):
            fail(f"Catalog tool {tool_name} must use an HTTPS Helm repository or OCI chart repository")
        if not isinstance(chart.get("version"), str) or not VERSION.fullmatch(chart["version"]):
            fail(f"Catalog tool {tool_name} has an invalid chart version")

    configured = {}
    for cluster_name in sorted(clusters):
        tools_dir = repo / "clusters" / cluster_name / "tools"
        for tool_dir in sorted(path for path in tools_dir.glob("*") if path.is_dir()):
            metadata_path = tool_dir / "tool.yaml"
            metadata = load_yaml(metadata_path)
            if not isinstance(metadata, dict):
                fail(f"Missing or invalid tool metadata: {metadata_path.relative_to(repo)}")
            tool_name = metadata.get("name")
            namespace = metadata.get("namespace", tool_name)
            dependencies = metadata.get("depends_on", [])
            if tool_name != tool_dir.name:
                fail(f"{metadata_path.relative_to(repo)} name must match its directory: {tool_dir.name}")
            validate_label(tool_name, f"{cluster_name} tool name")
            validate_label(namespace, f"{cluster_name}/{tool_name} namespace")
            if not isinstance(dependencies, list) or not all(isinstance(item, str) for item in dependencies):
                fail(f"{metadata_path.relative_to(repo)} depends_on must be a list of tool names")
            if len(dependencies) != len(set(dependencies)):
                fail(f"{metadata_path.relative_to(repo)} contains duplicate dependencies")
            for dependency in dependencies:
                validate_label(dependency, f"{cluster_name}/{tool_name} dependency")
                if dependency == tool_name:
                    fail(f"Tool {cluster_name}/{tool_name} cannot depend on itself")
            if tool_name not in tools:
                fail(f"Tool {tool_name} configured for {cluster_name} is missing from catalog/tools.yaml")
            values_path = tool_dir / "values.yaml"
            values = load_yaml(values_path)
            if values is not None and not isinstance(values, dict):
                fail(f"{values_path.relative_to(repo)} must contain a YAML mapping")
            resources_dir = values_path.parent / "resources"
            if resources_dir.exists():
                for manifest in sorted(resources_dir.glob("*.y*ml")):
                    with manifest.open(encoding="utf-8") as stream:
                        for document in yaml.safe_load_all(stream):
                            if document is None:
                                continue
                            if not isinstance(document, dict) or not document.get("apiVersion") or not document.get("kind"):
                                fail(f"Invalid Kubernetes document in {manifest.relative_to(repo)}")
                            if document["kind"] == "Secret":
                                fail(f"Plain Secret objects are not allowed: {manifest.relative_to(repo)}; use ExternalSecret")
                            declared_namespace = document.get("metadata", {}).get("namespace")
                            if declared_namespace and declared_namespace != namespace:
                                fail(
                                    f"{manifest.relative_to(repo)} targets namespace {declared_namespace}, expected {namespace}"
                                )
            configured[(cluster_name, tool_name)] = {
                "chart": tools[tool_name]["chart"],
                "cluster": cluster_name,
                "kind": "tool",
                "tool": tool_name,
                "namespace": namespace,
                "chart_version": tools[tool_name]["version"],
                "depends_on": dependencies,
            }
        baseline_dir = repo / "clusters" / cluster_name / "baseline"
        if not baseline_dir.is_dir():
            fail(f"Missing baseline directory: {baseline_dir.relative_to(repo)}")
        for manifest in sorted(baseline_dir.glob("*.y*ml")):
            with manifest.open(encoding="utf-8") as stream:
                for document in yaml.safe_load_all(stream):
                    if document is None:
                        continue
                    if not isinstance(document, dict) or not document.get("apiVersion") or not document.get("kind"):
                        fail(f"Invalid Kubernetes document in {manifest.relative_to(repo)}")
                    if document.get("metadata", {}).get("namespace"):
                        fail(f"Baseline object must not declare metadata.namespace: {manifest.relative_to(repo)}")

    for (cluster_name, tool_name), tool in sorted(configured.items()):
        for dependency in tool["depends_on"]:
            if (cluster_name, dependency) not in configured:
                fail(f"Tool {cluster_name}/{tool_name} depends on unknown tool {dependency}")

    visiting = set()
    visited = set()

    def visit(key, path):
        if key in visiting:
            cycle = " -> ".join([*(item[1] for item in path), key[1]])
            fail(f"Tool dependency cycle in {key[0]}: {cycle}")
        if key in visited:
            return
        visiting.add(key)
        for dependency in configured[key]["depends_on"]:
            visit((key[0], dependency), [*path, key])
        visiting.remove(key)
        visited.add(key)

    for key in sorted(configured):
        visit(key, [])

    files = changed_files(repo, commit, mode)
    baseline_targets = set()
    target_actions = defaultdict(set)
    catalog_changed = any(path == "catalog/tools.yaml" for path in files)
    for path in files:
        parts = Path(path).parts
        if len(parts) < 3 or parts[0] != "clusters":
            continue
        cluster_name = parts[1]
        if cluster_name not in clusters:
            fail(f"Unknown cluster path in changed file: {path}")
        if parts[2] == "baseline":
            if Path(path).name != "README.md":
                baseline_targets.add(cluster_name)
        elif len(parts) >= 5 and parts[2] == "tools":
            tool_name = parts[3]
            key = (cluster_name, tool_name)
            if key not in configured:
                fail(f"Changed path has no valid tool.yaml metadata: {path}")
            relative_parts = parts[4:]
            if Path(path).name == "README.md":
                continue
            if relative_parts[0] in ("tool.yaml", "values.yaml"):
                target_actions[key].add("helm")
            elif relative_parts[0] == "resources" or relative_parts[0] == "verify.sh":
                target_actions[key].add("resources")
            else:
                fail(f"Unsupported tool configuration path: {path}")
        else:
            fail(f"Unsupported cluster configuration path: {path}")

    if catalog_changed:
        for key in configured:
            target_actions[key].add("helm")

    # A changed prerequisite selects all downstream tools so dependency ordering
    # remains meaningful during incremental orchestrated deployments.
    selected = set(target_actions)
    expanded = True
    while expanded:
        expanded = False
        for key, tool in configured.items():
            dependency_keys = {(key[0], dependency) for dependency in tool["depends_on"]}
            if key not in selected and dependency_keys.intersection(selected):
                selected.add(key)
                target_actions[key].update(("helm", "resources"))
                expanded = True

    targets = [{"cluster": cluster, "kind": "baseline"} for cluster in sorted(baseline_targets)]
    action_order = {"helm": 0, "resources": 1}
    for key in sorted(selected):
        target = dict(configured[key])
        target["actions"] = sorted(target_actions[key], key=action_order.get)
        targets.append(target)

    return {
        "catalog_changed": catalog_changed,
        "commit": commit,
        "targets": sorted(targets, key=lambda item: (item["cluster"], item["kind"], item.get("tool", ""))),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--mode", choices=("changed", "all"), default="changed")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = validate(Path(args.repo).resolve(), args.commit, args.mode)
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Validated cluster administration configuration; selected {len(result['targets'])} target(s)")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        print(f"Configuration validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
