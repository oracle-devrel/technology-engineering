#!/usr/bin/env python3
"""Mirror images for selected Helm targets without changing chart values."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml


SKOPEO_IMAGE = "quay.io/skopeo/stable:v1.15.2"
PATH_PART = r"[a-z0-9]+(?:(?:[._]|__|-+)[a-z0-9]+)*"
REPOSITORY = re.compile(rf"{PATH_PART}(?:/{PATH_PART})*")
HOST = re.compile(r"[a-z0-9]+(?:[.-][a-z0-9]+)*(?::[0-9]{1,5})?")
DIGEST = re.compile(r"sha256:[a-f0-9]{64}")
TAG = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,127}")
LABEL = re.compile(r"[a-z0-9](?:[-a-z0-9]*[a-z0-9])?")


def image_reference(value):
    if not isinstance(value, str) or not value or re.search(r"\s|://", value):
        raise ValueError(f"Invalid container image reference: {value!r}")
    name, separator, digest = value.partition("@")
    if separator and not DIGEST.fullmatch(digest):
        raise ValueError(f"Image digest must be sha256: {value}")
    tag = None
    if ":" in name.rsplit("/", 1)[-1]:
        name, tag = name.rsplit(":", 1)
        if not TAG.fullmatch(tag):
            raise ValueError(f"Invalid image tag: {value}")
    first, slash, rest = name.partition("/")
    if slash and ("." in first or ":" in first or first == "localhost"):
        registry, repository = first.lower(), rest
    else:
        registry, repository = "docker.io", name
    if registry in ("index.docker.io", "registry-1.docker.io"):
        registry = "docker.io"
    if registry == "docker.io" and "/" not in repository:
        repository = "library/" + repository
    if not HOST.fullmatch(registry) or not REPOSITORY.fullmatch(repository):
        raise ValueError(f"Invalid image registry or repository: {value}")
    if ":" in registry and not 0 < int(registry.rsplit(":", 1)[1]) < 65536:
        raise ValueError(f"Invalid registry port: {value}")
    root = registry + "/" + repository
    reference = root + ("@" + digest if digest else ":" + (tag or "latest"))
    return {"registry": registry, "repository": repository, "root": root,
            "reference": reference, "digest": digest or None}


def pod_images(document):
    if not isinstance(document, dict):
        return set()
    kind = document.get("kind")
    if kind == "List":
        return set().union(*(pod_images(item) for item in document.get("items", [])))
    if kind == "Pod":
        spec = document.get("spec", {})
    elif kind == "CronJob":
        spec = document.get("spec", {}).get("jobTemplate", {}).get("spec", {}).get("template", {}).get("spec", {})
    elif kind in ("Deployment", "StatefulSet", "DaemonSet", "ReplicaSet", "ReplicationController", "Job"):
        spec = document.get("spec", {}).get("template", {}).get("spec", {})
    else:
        return set()
    images = set()
    for field in ("containers", "initContainers", "ephemeralContainers"):
        for container in spec.get(field, []) or []:
            value = container.get("image")
            if value:
                image_reference(value)
                images.add(value)
    return images


def snapshot(repo, commit, path):
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{commit}:{path}"])


def selected_targets(selection, catalog):
    targets = []
    for target in selection["targets"]:
        if target["kind"] != "tool" or "helm" not in target["actions"]:
            continue
        tool = target["tool"]
        chart = catalog["tools"][tool]
        if not isinstance(chart.get("mirror_images", False), bool):
            raise ValueError(f"{tool}: mirror_images must be boolean")
        if not chart.get("mirror_images", False):
            continue
        for name in (target["cluster"], tool, target["namespace"]):
            if not isinstance(name, str) or len(name) > 63 or not LABEL.fullmatch(name):
                raise ValueError(f"Invalid target name: {name!r}")
        if target["chart"] != chart["chart"] or target["chart_version"] != chart["version"]:
            raise ValueError(f"{tool}: selected chart does not match committed catalog")
        additional = chart.get("additional_images", [])
        if not isinstance(additional, list):
            raise ValueError(f"{tool}: additional_images must be a list")
        for image in additional:
            image_reference(image)
        targets.append(target)
    return sorted(targets, key=lambda item: (item["cluster"], item["tool"]))


class RegistryMirror:
    def __init__(self, registry, namespace, prefix, compartment, directory):
        if not HOST.fullmatch(registry) or not REPOSITORY.fullmatch(namespace + "/" + prefix):
            raise ValueError("Invalid destination registry, namespace or image prefix")
        self.registry, self.namespace, self.prefix = registry, namespace, prefix
        self.compartment = compartment
        self.auth_file = directory / "registry-auth.json"
        credentials = os.environ.get("REGISTRY_AUTH_FILE")
        config = json.loads(Path(credentials).read_text()) if credentials else {}
        payload = self.oci(["raw-request", "--http-method", "GET", "--target-uri",
                            f"https://{registry}/20180419/docker/token"])
        payload = payload.get("data", payload)
        payload = json.loads(payload) if isinstance(payload, str) else payload
        token = payload["token"]
        config.setdefault("auths", {})[registry] = {
            "auth": base64.b64encode(("BEARER_TOKEN:" + token).encode()).decode()
        }
        self.auth_file.write_text(json.dumps(config), encoding="utf-8")
        self.auth_file.chmod(0o600)
        self.helm_env = dict(os.environ, HELM_REGISTRY_CONFIG=str(directory / "helm-auth.json"))
        subprocess.run(["helm", "registry", "login", registry, "-u", "BEARER_TOKEN", "--password-stdin"],
                       input=token, text=True, stdout=subprocess.DEVNULL, check=True, env=self.helm_env)
        self.repositories = set()
        self.copies = {}

    @staticmethod
    def oci(arguments):
        return json.loads(subprocess.check_output(["oci", *arguments, "--output", "json"]))

    def skopeo(self, arguments):
        return subprocess.check_output([
            "docker", "run", "--rm", "--volume", f"{self.auth_file}:/auth/config.json:ro",
            SKOPEO_IMAGE, *arguments,
        ])

    def digest(self, reference):
        manifest = self.skopeo(["inspect", "--raw", "--authfile", "/auth/config.json", "docker://" + reference])
        return "sha256:" + hashlib.sha256(manifest).hexdigest()

    def ensure_repository(self, path):
        if path in self.repositories:
            return
        result = self.oci(["artifacts", "container", "repository", "list", "--compartment-id",
                           self.compartment, "--display-name", path, "--limit", "1"])
        if not result["data"]["items"]:
            self.oci(["artifacts", "container", "repository", "create", "--compartment-id",
                      self.compartment, "--display-name", path, "--is-public", "false",
                      "--freeform-tags", json.dumps({"owner": "cluster-administrators",
                          "purpose": "cluster-administration", "scope": "operations", "role": "image-repository"})])
        self.repositories.add(path)

    def mirror(self, source):
        image = image_reference(source)
        canonical = image["reference"]
        if canonical in self.copies:
            return dict(self.copies[canonical], source=source)
        digest = self.digest(canonical)
        if image["digest"] and image["digest"] != digest:
            raise ValueError(f"Source digest verification failed: {canonical}")
        if image["registry"] == self.registry and image["repository"].startswith(self.namespace + "/"):
            result = {"source": source, "source_digest": digest, "destination": canonical,
                      "destination_digest": digest, "destination_digest_reference": image["root"] + "@" + digest,
                      "status": "already-in-target-ocir"}
        else:
            path = f"{self.prefix}/{image['registry'].replace(':', '_')}/{image['repository']}"
            if len(path) > 255:
                raise ValueError(f"Destination repository path exceeds 255 characters: {path}")
            destination_root = f"{self.registry}/{self.namespace}/{path}"
            destination = destination_root + ":" + digest.replace(":", "-")
            self.ensure_repository(path)
            try:
                exists = self.digest(destination) == digest
            except subprocess.CalledProcessError:
                exists = False
            if not exists:
                self.skopeo(["copy", "--all", "--preserve-digests", "--authfile", "/auth/config.json",
                             "docker://" + image["root"] + "@" + digest, "docker://" + destination])
            actual = self.digest(destination)
            if actual != digest:
                raise ValueError(f"Destination digest verification failed: {destination}")
            result = {"source": source, "source_digest": digest, "destination": destination,
                      "destination_digest": actual, "destination_digest_reference": destination_root + "@" + digest,
                      "status": "exists" if exists else "copied"}
        self.copies[canonical] = result
        print(f"Image mirror: {source} -> {result['destination']}", flush=True)
        return dict(result)


def prepare_images(repo, selection, registry, namespace, image_prefix, chart_prefix, compartment, output_dir):
    commit = selection["commit"]
    if not re.fullmatch(r"[a-f0-9]{40,64}", commit):
        raise ValueError("Image mirroring requires a full configuration commit hash")
    catalog_bytes = snapshot(repo, commit, "catalog/tools.yaml")
    catalog = yaml.safe_load(catalog_bytes)
    targets = selected_targets(selection, catalog)
    output_dir.mkdir(parents=True, exist_ok=True)
    index = []
    if targets:
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            mirror = RegistryMirror(registry, namespace, image_prefix, compartment, work)
            for target in targets:
                cluster, tool = target["cluster"], target["tool"]
                values_bytes = snapshot(repo, commit, f"clusters/{cluster}/tools/{tool}/values.yaml")
                values_path = work / "values.yaml"
                values_path.write_bytes(values_bytes)
                chart = target["chart"].rstrip("/").rsplit("/", 1)[-1]
                reference = f"oci://{registry}/{namespace}/{chart_prefix}/{chart}"
                images = set(catalog["tools"][tool].get("additional_images", []))
                # Both lifecycle variants include conditional hook workloads.
                for lifecycle in ([], ["--is-upgrade"]):
                    rendered = subprocess.check_output([
                        "helm", "template", tool, reference, "--version", target["chart_version"],
                        "--namespace", target["namespace"], "--values", str(values_path), "--include-crds", *lifecycle,
                    ], env=mirror.helm_env)
                    for document in yaml.safe_load_all(rendered):
                        images.update(pod_images(document))
                mappings = [mirror.mirror(image) for image in sorted(images)]
                report = {"commit": commit, "cluster": cluster, "tool": tool, "chart": reference,
                          "chart_version": target["chart_version"],
                          "values_sha256": hashlib.sha256(values_bytes).hexdigest(), "images": mappings}
                report_path = output_dir / cluster / tool / "images.json"
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
                index.append({"cluster": cluster, "tool": tool, "path": str(report_path)})
    (output_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    return index


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--targets", type=Path, required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--tenancy-namespace", required=True)
    parser.add_argument("--image-prefix", required=True)
    parser.add_argument("--chart-prefix", required=True)
    parser.add_argument("--compartment-id", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    selection = json.loads(args.targets.read_text())
    prepare_images(args.repo, selection, args.registry, args.tenancy_namespace, args.image_prefix,
                   args.chart_prefix, args.compartment_id, args.output_dir)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"Image mirroring failed: {exc}", file=sys.stderr)
        sys.exit(1)
