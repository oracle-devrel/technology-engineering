"""Opt-in local Docker registry test; never accesses OCI."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import unittest
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("registry_image_mirror", ROOT / "repos/cluster-admin/script/mirror-images.py")
images = importlib.util.module_from_spec(spec)
spec.loader.exec_module(images)


@unittest.skipUnless(os.environ.get("RUN_IMAGE_MIRROR_REGISTRY_TEST") == "1", "Set RUN_IMAGE_MIRROR_REGISTRY_TEST=1 for local Docker integration")
class RegistryIntegrationTest(unittest.TestCase):
    def test_real_multiplatform_copy_and_repeat(self):
        suffix = uuid.uuid4().hex[:10]
        network = "mirror-test-" + suffix
        source, target = "mirror-source-" + suffix, "mirror-target-" + suffix
        containers = []
        def docker(*args, **kwargs):
            return subprocess.check_output(["docker", *args], **kwargs)
        docker("network", "create", network)
        try:
            for name in (source, target):
                docker("run", "-d", "--name", name, "--network", network, "-p", "127.0.0.1::5000", "registry:2")
                containers.append(name)
                port = docker("port", name, "5000/tcp", text=True).strip().rsplit(":", 1)[1]
                for attempt in range(30):
                    try:
                        with urllib.request.urlopen("http://127.0.0.1:" + port + "/v2/", timeout=1):
                            break
                    except OSError:
                        if attempt == 29:
                            raise
                        time.sleep(0.5)
            with tempfile.TemporaryDirectory() as directory:
                auth = Path(directory) / "auth.json"
                auth.write_text('{"auths":{}}')
                def skopeo(arguments):
                    arguments = list(arguments)
                    # Plain HTTP is limited to the disposable local test registries.
                    if arguments[0] == "copy":
                        arguments[1:1] = ["--src-tls-verify=false", "--dest-tls-verify=false"]
                    else:
                        arguments[1:1] = ["--tls-verify=false"]
                    return docker("run", "--rm", "--network", network, "--volume", str(auth) + ":/auth/config.json:ro", images.SKOPEO_IMAGE, *arguments)
                # The upstream copy retains normal TLS verification.
                docker("run", "--rm", "--network", network, images.SKOPEO_IMAGE,
                       "copy", "--all", "--preserve-digests", "--dest-tls-verify=false",
                       "docker://docker.io/library/busybox:1.36.1", "docker://" + source + ":5000/team/busybox:v1")
                client = images.RegistryMirror.__new__(images.RegistryMirror)
                client.registry, client.namespace, client.prefix = target + ":5000", "namespace", "project/images"
                client.copies, client.repositories = {}, set()
                client.skopeo = skopeo
                client.ensure_repository = lambda path: None
                result = client.mirror(source + ":5000/team/busybox:v1")
                raw = skopeo(["inspect", "--raw", "--authfile", "/auth/config.json", "docker://" + result["destination"]])
                manifest = json.loads(raw)
                self.assertGreater(len(manifest["manifests"]), 1)
                architectures = {entry.get("platform", {}).get("architecture") for entry in manifest["manifests"]}
                self.assertTrue({"amd64", "arm64"}.issubset(architectures))
                self.assertEqual(result["source_digest"], result["destination_digest"])
                self.assertEqual(result["status"], "copied")
                client.copies.clear()
                self.assertEqual(client.mirror(source + ":5000/team/busybox:v1")["status"], "exists")
        finally:
            for name in containers:
                subprocess.run(["docker", "rm", "-f", name], check=False, stdout=subprocess.DEVNULL)
            subprocess.run(["docker", "network", "rm", network], check=False, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    unittest.main()
