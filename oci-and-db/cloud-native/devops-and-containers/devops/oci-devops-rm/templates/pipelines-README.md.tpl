# Pipelines

This repository contains reusable OCI DevOps build specs and helper scripts for the ${application_name} delivery flow.

It is the primary source for shared build pipelines. The component source repository and chart repository are checked out as secondary sources when a pipeline needs them.

Generated build specs:

- `${component_name}-build-pipeline.yaml` builds component source changes, packages that component chart when needed, and exports deployment parameters for dev.
- `${application_name}-package-pipeline.yaml` packages the `${application_name}` umbrella baseline chart and starts the baseline deployment pipeline.
- `${component_name}-release-pipeline.yaml` creates the OCI DevOps Git tag, retags the matching 7-character SHA image as a SemVer release candidate such as `1.0.0-rc.1`, and starts the component release deployment.
- `helm-chart-pipeline.yaml` is a generic chart packager retained for future reuse.

Resource Manager seeds these files as starter content. Existing files are developer-owned and are never overwritten by later stack applies.

Components may instead configure `build_spec_path` in the Resource Manager applications JSON. An explicit path can be shared, for example `java/java-build-pipeline.yaml`. Resource Manager creates the file and parent folders from the default template only when missing, giving the DevOps engineer a working base. The path becomes user-owned after that first commit and is never refreshed or overwritten.

The build specs should stay readable and macro-oriented. Detailed branching, registry checks, chart parsing, image promotion, and release input resolution belong in `script/*.sh`.

Default pipeline names:

- `${component_name}-build`
- `${application_name}-package`
- `${component_name}-pr`
- `${component_name}-release-build`
