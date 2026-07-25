# Component Source Repository

This repository is the generated source repository for one application component.

For the default sample it is named `sample-component`. It contains starter application code, a Dockerfile, and the component-owned pull request pipeline build spec.

## Important Files

- `Dockerfile`: image build definition used by `<component>-build`.
- `.oci-devops/application.env`: component identity read by the shared build pipeline.
- `.oci-devops/pull-request-pipeline.yaml`: component-owned PR validation build spec.

Do not put Helm charts or values here. Chart changes belong in the application chart repository, by default `<application>-chart`.

## Developer Responsibilities

The pull request pipeline spec is intentionally a placeholder. Testing strategies depend on the component language, framework, and integration boundaries, so replace `.oci-devops/pull-request-pipeline.yaml` with the checks that make sense for this component.

The shared build pipeline expects the component build to be described by the `Dockerfile`. Prefer a multi-stage Dockerfile so compilation, dependency installation, and build tooling stay in builder stages while the final runtime image stays small and production-focused.

## Development Flow

1. Open a pull request to `main`.
2. `<component>-pr` runs the component-owned checks.
3. After merge, `<component>-build` builds a multi-architecture image tagged with the 7-character commit SHA.
4. The successful build deploys the dev release.
5. Run `<component>-release-build` with a release candidate tag such as `1.0.0-rc.1` to promote the selected image.

The build pipeline reads this contract file:

```bash
component_name=<component>
```

Images are pushed to:

```text
<region-key>.ocir.io/<tenancy-namespace>/<devops-project>/<application>/<component>:<sha7>
```
