#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml


def operation_tags(**dimensions):
    tags = {
        "owner": "cluster-administrators",
        "purpose": "cluster-administration",
        "scope": "operations",
    }
    tags.update({key: value for key, value in dimensions.items() if value})
    return tags


def run(command, **kwargs):
    print("+", " ".join(command))
    return subprocess.run(command, check=True, text=True, **kwargs)


def output(command):
    return subprocess.check_output(command, text=True).strip()


def source_reference(repository, chart, alias):
    if repository.startswith("oci://"):
        return f"{repository.rstrip('/')}/{chart.lstrip('/')}"
    return f"{alias}/{chart}"


def target_chart_name(chart):
    return chart.rstrip("/").rsplit("/", 1)[-1]


def only_path(paths, description):
    paths = list(paths)
    if len(paths) != 1:
        raise ValueError(f"Expected exactly one {description}, found {len(paths)}")
    return paths[0]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", required=True)
    parser.add_argument("--compartment-id", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--tenancy-namespace", required=True)
    parser.add_argument("--target-prefix", required=True)
    args = parser.parse_args()

    catalog = yaml.safe_load(Path(args.catalog).read_text(encoding="utf-8"))
    tools = catalog["tools"]
    token_response = output(
        ["oci", "raw-request", "--http-method", "GET", "--target-uri", f"https://{args.registry}/20180419/docker/token"]
    )
    payload = json.loads(token_response)
    if isinstance(payload.get("data"), str):
        payload = json.loads(payload["data"])
    elif isinstance(payload.get("data"), dict):
        payload = payload["data"]
    token = payload["token"]
    run(["helm", "registry", "login", args.registry, "-u", "BEARER_TOKEN", "--password-stdin"], input=token)

    target_root = f"oci://{args.registry}/{args.tenancy_namespace}/{args.target_prefix}"
    with tempfile.TemporaryDirectory() as temp_dir:
        for tool_name, chart in sorted(tools.items()):
            version = chart["version"]
            target_name = target_chart_name(chart["chart"])
            target = f"{target_root}/{target_name}"
            exists = subprocess.run(
                ["helm", "show", "chart", target, "--version", version],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            ).returncode == 0
            if exists:
                print(f"Chart already mirrored: {tool_name}:{version}")
                continue

            repository_path = f"{args.target_prefix}/{target_name}"
            existing_id = output([
                "oci", "artifacts", "container", "repository", "list",
                "--compartment-id", args.compartment_id,
                "--display-name", repository_path,
                "--limit", "1",
                "--query", "data.items[0].id",
                "--raw-output",
            ])
            if existing_id in ("", "null", "None"):
                run([
                    "oci", "artifacts", "container", "repository", "create",
                    "--compartment-id", args.compartment_id,
                    "--display-name", repository_path,
                    "--freeform-tags", json.dumps(operation_tags(role="chart-repository", tool=tool_name)),
                ], stdout=subprocess.DEVNULL)

            repository = chart["repository"]
            alias = f"mirror-{tool_name}"
            if repository.startswith("https://"):
                run(["helm", "repo", "add", alias, repository, "--force-update"])

            source = source_reference(repository, chart["chart"], alias)
            extract_dir = Path(temp_dir) / tool_name
            extract_dir.mkdir()
            run([
                "helm", "pull", source,
                "--version", version,
                "--untar",
                "--untardir", str(extract_dir),
            ])

            chart_dir = only_path(
                (path for path in extract_dir.iterdir() if path.is_dir()),
                f"extracted chart directory for {tool_name}",
            )
            chart_yaml = chart_dir / "Chart.yaml"
            chart_metadata = yaml.safe_load(chart_yaml.read_text(encoding="utf-8"))
            annotations = chart_metadata.get("annotations", {})
            safe_annotations = {
                key: value for key, value in annotations.items() if str(value).isascii()
            }
            if safe_annotations != annotations:
                print(f"Removed non-ASCII OCI annotations before mirroring {tool_name}:{version}")
                if safe_annotations:
                    chart_metadata["annotations"] = safe_annotations
                else:
                    chart_metadata.pop("annotations", None)
                chart_yaml.write_text(
                    yaml.safe_dump(chart_metadata, sort_keys=False), encoding="utf-8"
                )

            package_dir = Path(temp_dir) / "packages"
            package_dir.mkdir(exist_ok=True)
            existing_archives = set(package_dir.glob("*.tgz"))
            run(["helm", "package", str(chart_dir), "--destination", str(package_dir)])
            archive = only_path(
                set(package_dir.glob("*.tgz")) - existing_archives,
                f"packaged chart archive for {tool_name}",
            )
            run(["helm", "push", str(archive), target_root])
            run(["helm", "show", "chart", target, "--version", version], stdout=subprocess.DEVNULL)
            print(f"Mirrored chart: {tool_name}:{version}")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, ValueError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"Chart mirroring failed: {exc}", file=sys.stderr)
        sys.exit(1)
