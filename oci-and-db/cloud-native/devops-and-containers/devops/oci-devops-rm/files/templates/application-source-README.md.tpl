# ${component_name}

This repository contains the source code for the `${component_name}` component.

Use this repository for application code, tests, and the component-owned pull request build spec. Do not put Helm charts or values here; chart changes belong in the separate `${chart_repository_name}` repository.

Important files:

- `Dockerfile`: image build definition used by `${component_name}-build`.
- `.oci-devops/application.env`: component identity read by the shared build pipeline.
- `.oci-devops/pull-request-pipeline.yaml`: component-owned PR validation build spec.

Developer responsibilities:

- The pull request pipeline spec is intentionally a placeholder. Testing strategies depend on the component language, framework, and integration boundaries, so replace `.oci-devops/pull-request-pipeline.yaml` with the checks that make sense for this component.
- The shared build pipeline expects the component build to be described by the `Dockerfile`. Prefer a multi-stage Dockerfile so compilation, dependency installation, and build tooling stay in builder stages while the final runtime image stays small and production-focused.

Normal development flow:

1. Open a pull request to `main`.
2. The `${component_name}-pr` pipeline runs the component-owned checks.
3. After merge, `${component_name}-build` builds a multi-architecture image tagged with the 7-character commit SHA.
4. The successful build deploys the dev release.
5. Run `${component_name}-release-build` with a release candidate tag such as `1.0.0-rc.1` to promote the selected image.
6. After production deployment and final Git tagging, OCI DevOps finishes by reporting the Helm release status, resources, history, notes, and namespace release listing.

The build pipeline reads this contract file:

```bash
component_name=${component_name}
```

Images are pushed to:

```text
<region-key>.ocir.io/<tenancy-namespace>/${devops_project_prefix}/${application_name}/${component_name}:<sha7>
```
