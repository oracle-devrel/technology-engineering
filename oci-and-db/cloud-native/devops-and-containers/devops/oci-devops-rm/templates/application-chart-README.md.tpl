# ${chart_repository_name}

This repository contains Helm charts for the `${application_name}` application.

The umbrella chart and component charts have separate lifecycles:

- `${application_path}` is the `${application_name}` umbrella chart. It owns shared namespace baseline resources.
- `${application_path}/charts/${component_name}` is the `${component_name}` component chart. It owns the component `Deployment`, `Service`, and `ServiceAccount`.
- `${application_path}/.helmignore` excludes `charts/` when the baseline is packaged, so component charts are never installed by the umbrella release.

Trigger behavior:

- Changes under `${application_path}/charts/${component_name}/**` package only the component chart and redeploy dev.
- Changes under `${application_path}/**`, excluding `charts/**`, package only the umbrella baseline chart and start `${application_name}-deploy`.
- Source code changes are handled in the separate `${component_name}` source repository.

The umbrella chart has no component dependencies. Component environments are deployed by installing each component chart directly with environment-specific values.
