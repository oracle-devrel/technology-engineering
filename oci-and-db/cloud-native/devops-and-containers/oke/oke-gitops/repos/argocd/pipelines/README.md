# Pipeline Repository

This repository contains OCI DevOps build specifications and shared scripts used to mirror external artifacts into OCIR.

## First run after creating the stack

The stack creates `bootstrap-gitops-agent` for the first installation and
`mirror-gitops-agent` for later mirroring. Start `bootstrap-gitops-agent` from
the OCI DevOps Console. It runs `mirror_argocd.yaml`, mirrors the Argo CD chart
and images, and automatically triggers `install-gitops-agent`. That deployment
prepares the namespace and Vault-backed credentials and installs Argo CD. It
deliberately stops there.
Clone `cluster-config` and run
`kubectl apply -f bootstrap/argocd-bootstrap.yml` to start Git reconciliation.

Create two OCI Vault secrets before starting the build. The Git secret must
contain a dedicated read-only OCI DevOps repository identity:

```json
{"username":"<tenancy>/<domain>/<gitops-reader>","password":"<git-reader-auth-token>"}
```

The OCIR secret must contain a different pull-only registry identity:

```json
{"username":"<tenancy-namespace>/<domain>/<ocir-reader>","password":"<ocir-reader-auth-token>"}
```

Set `git_read_credentials_secret_ocid` and
`registry_pull_secret_ocid` to their respective Secret OCIDs. The
build passes only the OCIDs to `install-gitops-agent`; the deployment reads the
values directly from Vault. `auth_token_secret_ocid` is a deprecated
one-release fallback for existing stacks and must not be used for new
installations. Leave `chart_version` at its `LATEST` default, or provide the
exact chart version to bootstrap.

Wait for the build and deployment runs to succeed; do not manually start a
duplicate deployment.

The mirroring build specs included here are examples. They are intended to show the pattern for common use cases, not to be the only pipelines used in a real platform.

Included examples:
- `mirror_argocd.yaml`: mirrors the selected Argo CD Helm chart and the images rendered by that chart.
- `mirror_helm.yaml`: mirrors a Helm chart and the images rendered by that chart.
- `mirror_images.yaml`: mirrors a list of container images.
- `mirror_git_dr.yaml`: mirrors this Git repository to a secondary repository for DR scenarios.
- `script/`: shared helper scripts used by the build specs.

For an upgrade, run `mirror-gitops-agent`. Its only parameter is
`chart_version`: leave `LATEST` to resolve the current upstream release or set
an exact version. It publishes the selected chart and all rendered images to
OCIR and stops; it never triggers `install-gitops-agent`. The self-managed Argo
CD Application consumes the newest chart available in that private repository.
This parameter does not change Git. To pin or roll back, first mirror the exact
version, then commit that version in the self-management descriptor.

## Recommended Layout for Custom Mirroring
When creating mirroring pipelines for infrastructure applications, create a dedicated folder:

```text
mirroring/
  external-secrets.yaml
  ingress-nginx.yaml
  cert-manager.yaml
  custom-images.yaml
```

Each file should be a complete OCI DevOps build specification. Start by copying one of the examples, then customize the variables and steps for the artifact you want to mirror.

## Create a Mirroring Pipeline

### 1. Choose What to Mirror
Use one of these starting points:

- Helm chart and chart images: copy `mirror_helm.yaml`.
- Only images rendered by a Helm chart: copy `mirror_helm.yaml` and keep only the load variables and image mirroring stages.
- Explicit list of images: copy `mirror_images.yaml`.

### 2. Create a Build Spec
Create a file under `mirroring/`, for example:

```text
mirroring/external-secrets.yaml
```

Set the variables in the copied build spec:

```yaml
chart_name: "external-secrets"
chart_repo: "https://charts.external-secrets.io"
chart_version: "0.10.0"
```

For an image-only pipeline, set the image list instead:

```yaml
images_to_mirror: "docker.io/library/nginx:1.27.5,quay.io/example/app:1.0.0"
```

The common values `repo_compartment_id`, `repo_prefix`, and `region` are loaded from `variables.sh`.

### 3. Commit the Build Spec
Commit the new file to this repository:

```bash
git add mirroring/external-secrets.yaml
git commit -m "Add external-secrets mirror pipeline"
git push origin main
```

### 4. Create the OCI DevOps Build Pipeline
In OCI DevOps:

1. Open the DevOps project created by the stack.
2. Create a new Build Pipeline.
3. Add a Managed Build stage.
4. Select this `pipelines` repository as the source.
5. Select branch `main`.
6. Set the build spec path to your file, for example `mirroring/external-secrets.yaml`.
7. Use the same build image family used by the examples.
8. Save and run the pipeline.

### 5. Verify the Mirror
After the run succeeds:

1. Open OCIR in the target region.
2. Confirm the chart exists under `<repo_prefix>/charts/<chart-name>` when mirroring a Helm chart.
3. Confirm images exist under `<repo_prefix>/<image-name>` when mirroring images.
4. Update the corresponding GitOps configuration to consume the mirrored OCIR artifacts.

## Notes
- Keep public artifact mirroring in OCI DevOps pipelines so clusters pull from OCIR instead of public registries.
- Prefer one build spec per infrastructure application or logical artifact group.
- Pin chart and image versions for production pipelines.
- Use pull requests and review before promoting mirroring changes.
