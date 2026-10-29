#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def operation_tags(**dimensions):
    tags = {
        "owner": "cluster-administrators",
        "purpose": "cluster-administration",
        "scope": "operations",
    }
    tags.update({key: value for key, value in dimensions.items() if value})
    return tags


def oci(arguments):
    command = ["oci", *arguments, "--output", "json"]
    print("+", " ".join(command), flush=True)
    return json.loads(subprocess.check_output(command, text=True))


def ensure_mirrors(pipeline_id, commit, repository_url):
    result = oci([
        "devops", "build-run", "create",
        "--build-pipeline-id", pipeline_id,
        "--display-name", "Mirror cluster tool charts",
        "--commit-info", json.dumps({"commitHash": commit, "repositoryBranch": "main", "repositoryUrl": repository_url}),
        "--build-run-arguments", json.dumps({"items": [{"name": "config_commit", "value": commit}]}),
        "--freeform-tags", json.dumps(operation_tags(role="chart-mirror")),
        "--wait-for-state", "SUCCEEDED",
        "--wait-for-state", "FAILED",
        "--max-wait-seconds", "3600",
    ])
    state = result["data"]["lifecycle-state"]
    if state != "SUCCEEDED":
        raise RuntimeError(f"Chart mirror build finished in state {state}")


def mirror_selected_images(args, repo, selection):
    with tempfile.TemporaryDirectory() as directory:
        subprocess.run([
            sys.executable, str(repo / "script/mirror-images.py"), "--repo", str(repo),
            "--targets", args.targets, "--registry", args.registry,
            "--tenancy-namespace", args.tenancy_namespace, "--image-prefix", args.image_prefix,
            "--chart-prefix", args.chart_prefix, "--compartment-id", args.compartment_id,
            "--output-dir", directory,
        ], check=True)
        for report in json.loads((Path(directory) / "index.json").read_text()):
            upload_artifact(
                args.artifact_repository_id, args.compartment_id,
                f"cluster-admin/{report['cluster']}/tools/{report['tool']}/images.json",
                selection["commit"], Path(report["path"]), "image mapping",
            )


def publish_values(args, repo, target, commit):
    cluster, tool = target["cluster"], target["tool"]
    relative = f"clusters/{cluster}/tools/{tool}/values.yaml"
    content = subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{relative}"])
    with tempfile.TemporaryDirectory() as directory:
        values = Path(directory) / "values.yaml"
        values.write_bytes(content)
        upload_artifact(args.artifact_repository_id, args.compartment_id,
                        f"cluster-admin/{cluster}/tools/{tool}/values.yaml", commit, values, "values")


def upload_artifact(repository_id, compartment_id, artifact_path, version, source, label):
    existing = oci([
        "artifacts", "generic", "artifact", "list",
        "--compartment-id", compartment_id,
        "--repository-id", repository_id,
        "--artifact-path", artifact_path,
        "--artifact-version", version,
        "--limit", "1",
    ])["data"]["items"]
    if existing:
        print(f"{label} artifact already exists: {artifact_path}:{version}")
        return
    oci([
        "artifacts", "generic", "artifact", "upload-by-path",
        "--repository-id", repository_id,
        "--artifact-path", artifact_path,
        "--artifact-version", version,
        "--content-body", str(source),
    ])
    print(f"Published {label} artifact: {artifact_path}:{version}")


def resource_tags(resource):
    return resource.get("freeform-tags") or resource.get("free-form-tags") or {}


def pipeline_ids_by_cluster(project_id):
    pipelines = oci([
        "devops", "deploy-pipeline", "list",
        "--project-id", project_id,
        "--all",
    ])["data"]["items"]
    result = {}
    for pipeline in pipelines:
        tags = resource_tags(pipeline)
        cluster = tags.get("cluster")
        if (
            tags.get("purpose") == "cluster-administration"
            and tags.get("role") == "cluster-pipeline"
            and cluster
        ):
            result[cluster] = pipeline["id"]
        elif pipeline.get("display-name", "").startswith("cluster-admin-"):
            result.setdefault(pipeline["display-name"].removeprefix("cluster-admin-"), pipeline["id"])
    return result


def pipeline_arguments(pipeline_id, commit):
    pipeline = oci([
        "devops", "deploy-pipeline", "get",
        "--pipeline-id", pipeline_id,
    ])["data"]
    parameters = pipeline.get("deploy-pipeline-parameters", {}).get("items", [])
    arguments = {
        parameter["name"]: parameter.get("default-value") or "unused"
        for parameter in parameters
    }
    arguments["config_commit"] = commit
    return arguments


def run_pipeline(pipeline_id, cluster, commit, arguments, plan_summary=""):
    display_name = f"Deploy {cluster} changes {commit[:7]}"
    if plan_summary:
        display_name = f"{display_name}: {plan_summary}"[:255]
    deployment_arguments = {
        "items": [{"name": name, "value": value} for name, value in sorted(arguments.items())]
    }
    result = oci([
        "devops", "deployment", "create-pipeline-deployment",
        "--pipeline-id", pipeline_id,
        "--display-name", display_name,
        "--deployment-arguments", json.dumps(deployment_arguments),
        "--freeform-tags", json.dumps(
            operation_tags(
                cluster=cluster,
                role="cluster-deployment",
                config_commit=commit,
                targets=plan_summary[:255],
            )
        ),
        "--wait-for-state", "SUCCEEDED",
        "--wait-for-state", "FAILED",
        "--max-wait-seconds", "36000",
    ])
    state = result["data"]["lifecycle-state"]
    if state != "SUCCEEDED":
        raise RuntimeError(f"Cluster deployment for {cluster} finished in state {state}")
    print(f"Completed cluster deployment: {cluster}")


def dependency_waves(targets):
    pending = {target["tool"]: target for target in targets}
    completed = set()
    while pending:
        ready = [
            target for target in pending.values()
            if all(dependency not in pending or dependency in completed for dependency in target["depends_on"])
        ]
        if not ready:
            raise RuntimeError(f"Unable to order selected tools: {', '.join(sorted(pending))}")
        yield sorted(ready, key=lambda target: target["tool"])
        for target in ready:
            pending.pop(target["tool"])
            completed.add(target["tool"])


def cluster_plan(cluster, targets, commit):
    lines = [f"Cluster: {cluster}", f"Configuration commit: {commit}"]
    tool_targets = [target for target in targets if target["kind"] == "tool"]
    for number, wave in enumerate(dependency_waves(tool_targets), start=1):
        lines.append(f"Wave {number}:")
        for target in wave:
            actions = " + ".join(target["actions"])
            details = [f"namespace={target['namespace']}"]
            if "helm" in target["actions"]:
                details.extend((
                    f"chart={target['chart_version']}",
                    f"values={commit}",
                ))
            lines.append(f"  - {target['tool']}: {actions} ({', '.join(details)})")
    if any(target["kind"] == "baseline" for target in targets):
        lines.extend(("Final:", "  - cluster baseline"))
    if len(lines) == 2:
        lines.append("No deployment stages selected")
    return "\n".join(lines)


def plan_summary(targets):
    parts = []
    for target in sorted(targets, key=lambda item: (item["kind"], item.get("tool", ""))):
        if target["kind"] == "baseline":
            parts.append("baseline")
        else:
            parts.append(f"{target['tool']}[{'+'.join(target['actions'])}]")
    return ", ".join(parts)


def print_execution_plan(selection):
    targets_by_cluster = {}
    for target in selection["targets"]:
        targets_by_cluster.setdefault(target["cluster"], []).append(target)
    print("\n=== Cluster Administration Execution Plan ===", flush=True)
    if not targets_by_cluster:
        print(f"Configuration commit: {selection['commit']}")
        print("No cluster deployment stages selected", flush=True)
        return
    for cluster, targets in sorted(targets_by_cluster.items()):
        print(cluster_plan(cluster, targets, selection["commit"]), flush=True)
        print(flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--targets", required=True)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--mirror-pipeline-id", required=True)
    parser.add_argument("--artifact-repository-id", required=True)
    parser.add_argument("--compartment-id", required=True)
    parser.add_argument("--repository-url", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--tenancy-namespace", required=True)
    parser.add_argument("--chart-prefix", required=True)
    parser.add_argument("--image-prefix", required=True)
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    selection = json.loads(Path(args.targets).read_text(encoding="utf-8"))
    commit = selection["commit"]
    print_execution_plan(selection)
    targets_by_cluster = {}
    for target in selection["targets"]:
        targets_by_cluster.setdefault(target["cluster"], []).append(target)

    helm_targets = [
        target for target in selection["targets"]
        if target["kind"] == "tool" and "helm" in target["actions"]
    ]
    if selection["catalog_changed"] or helm_targets:
        ensure_mirrors(args.mirror_pipeline_id, commit, args.repository_url)
    if helm_targets:
        mirror_selected_images(args, repo, selection)

    for target in helm_targets:
        publish_values(args, repo, target, commit)

    if targets_by_cluster:
        upload_artifact(
            args.artifact_repository_id,
            args.compartment_id,
            "cluster-admin/deployment-plan.json",
            commit,
            Path(args.targets),
            "deployment plan",
        )

    pipeline_ids = pipeline_ids_by_cluster(args.project_id)
    for cluster, targets in sorted(targets_by_cluster.items()):
        pipeline_id = pipeline_ids.get(cluster)
        if not pipeline_id:
            raise RuntimeError(f"Cluster deployment pipeline not found: cluster-admin-{cluster}")
        base_arguments = pipeline_arguments(pipeline_id, commit)

        run_pipeline(
            pipeline_id,
            cluster,
            commit,
            base_arguments,
            plan_summary(targets),
        )


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Publish and dispatch failed: {exc}", file=sys.stderr)
        sys.exit(1)
