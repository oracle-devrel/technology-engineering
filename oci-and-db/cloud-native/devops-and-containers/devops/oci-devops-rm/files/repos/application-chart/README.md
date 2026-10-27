# Application Chart Repository

This repository is the generated Helm chart repository for an application.

For the default sample it is named `sample-app-chart` and contains the `sample-app` umbrella chart plus the `sample-component` component chart.

## Layout

```text
<application>/
  Chart.yaml
  values.yaml
  .helmignore
  charts/
    <component>/
      Chart.yaml
      values.yaml
      templates/
```

## Lifecycles

The umbrella chart and component charts have separate lifecycles:

- `<application>` is the umbrella baseline chart. It owns shared namespace resources.
- `<application>/charts/<component>` is the component chart. It owns the component `Deployment`, `Service`, and `ServiceAccount`.

Trigger behavior:

- Changes under `<application>/charts/<component>/**` package only that component chart and redeploy dev.
- Changes under `<application>/**`, excluding `charts/**`, package only the umbrella baseline chart and start `<application>-deploy`.
- Source code changes are handled in the separate `<component>` source repository.

The umbrella chart has no component dependencies, and `.helmignore` excludes `charts/` from baseline loading and packaging. Component environments are deployed by installing each component chart directly with environment-specific values.

Resource Manager adds missing application/component starter paths but never overwrites an existing repository path.
