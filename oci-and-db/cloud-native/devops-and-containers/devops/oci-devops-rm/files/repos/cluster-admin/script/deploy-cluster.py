#!/usr/bin/env python3
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

def run(command, **kwargs):
    print("+", " ".join(str(item) for item in command), flush=True)
    return subprocess.run(command, check=True, universal_newlines=True, **kwargs)


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


def deploy_tool(args, target, work_dir):
    tool = target["tool"]
    namespace = target["namespace"]
    actions = set(target["actions"])
    tool_dir = args.repo / "clusters" / args.cluster / "tools" / tool

    if "helm" in actions:
        values_file = work_dir / f"{tool}-values.yaml"
        run([
            "oci", "artifacts", "generic", "artifact", "download-by-path",
            "--repository-id", args.artifact_repository_id,
            "--artifact-path", f"cluster-admin/{args.cluster}/tools/{tool}/values.yaml",
            "--artifact-version", args.commit,
            "--file", str(values_file),
        ])
        chart_name = target["chart"].rstrip("/").rsplit("/", 1)[-1]
        chart_url = (
            f"oci://{args.registry}/{args.tenancy_namespace}/"
            f"{args.chart_prefix}/{chart_name}"
        )
        run([
            "helm", "upgrade", "--install", tool, chart_url,
            "--version", target["chart_version"],
            "--namespace", namespace,
            "--create-namespace",
            "--values", str(values_file),
            "--atomic",
            "--wait",
            "--timeout", "10m",
            "--history-max", "10",
        ])

    if "resources" in actions:
        resources_dir = tool_dir / "resources"
        manifests = sorted(resources_dir.glob("*.y*ml")) if resources_dir.is_dir() else []
        if manifests:
            run([
                "kubectl", "apply", "--server-side",
                "--field-manager=oci-devops-cluster-admin",
                "--namespace", namespace,
                "--filename", str(resources_dir),
            ])
        else:
            print(f"No supplemental resources to apply for {args.cluster}/{tool}")

        verify = tool_dir / "verify.sh"
        if verify.is_file():
            environment = dict(os.environ, NAMESPACE=namespace)
            run(["bash", str(verify)], env=environment)

    run(["helm", "status", tool, "--namespace", namespace])


def apply_baseline(args):
    baseline_dir = args.repo / "clusters" / args.cluster / "baseline"
    manifests = sorted(baseline_dir.glob("*.y*ml"))
    if not manifests:
        print(f"No baseline manifests to apply for {args.cluster}")
        return
    run([
        "kubectl", "apply", "--server-side",
        "--field-manager=oci-devops-cluster-admin",
        "--filename", str(baseline_dir),
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--cluster", default="prod")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--artifact-repository-id", required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--tenancy-namespace", required=True)
    parser.add_argument("--chart-prefix", required=True)
    args = parser.parse_args()

    selection = json.loads(args.targets.read_text(encoding="utf-8"))
    if selection["commit"] != args.commit:
        raise RuntimeError("Validated target commit does not match the deployment commit")
    targets = [target for target in selection["targets"] if target["cluster"] == args.cluster]
    tool_targets = [target for target in targets if target["kind"] == "tool"]
    with tempfile.TemporaryDirectory() as temp_dir:
        work_dir = Path(temp_dir)
        for number, wave in enumerate(dependency_waves(tool_targets), start=1):
            print(
                f"Deploying {args.cluster} tool wave {number}: "
                f"{', '.join(target['tool'] for target in wave)}",
                flush=True,
            )
            with ThreadPoolExecutor(max_workers=len(wave)) as executor:
                futures = [
                    executor.submit(deploy_tool, args, target, work_dir)
                    for target in wave
                ]
                for future in futures:
                    future.result()

    if any(target["kind"] == "baseline" for target in targets):
        apply_baseline(args)
    print(f"Cluster administration completed for {args.cluster} at {args.commit}")


if __name__ == "__main__":
    try:
        main()
    except (KeyError, OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Cluster deployment failed: {exc}", file=sys.stderr)
        sys.exit(1)
