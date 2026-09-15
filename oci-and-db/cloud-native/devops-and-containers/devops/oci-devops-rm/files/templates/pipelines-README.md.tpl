# Pipelines

This repository contains reusable OCI DevOps build specs and helper scripts for ${application_name}.

It is the primary source for shared build pipelines. Component source repositories are checked out as secondary sources; in full delivery mode, chart repositories are included only in stages that need them.

Generated build specs:

%{ if delivery_enabled ~}
- `${component_name}-build-pipeline.yaml` builds component source changes, packages that component chart when needed, and exports deployment parameters for dev.
- `${application_name}-package-pipeline.yaml` packages the `${application_name}` umbrella baseline chart and starts the baseline deployment pipeline.
- `${component_name}-release-pipeline.yaml` creates the OCI DevOps Git tag, retags the matching 7-character SHA image as a SemVer release candidate such as `1.0.0-rc.1`, and starts the component release deployment.
- `helm-chart-pipeline.yaml` is a generic chart packager retained for future reuse.
%{ else ~}
- `${component_name}-build-pipeline.yaml` builds and publishes a multi-architecture component image tagged with the 7-character Git SHA.

Build-only mode intentionally contains no chart packaging, release promotion, OKE deployment, or cluster administration specifications. Deployment configuration belongs to the external delivery system.
%{ endif ~}

Resource Manager seeds these files as starter content. Existing files are developer-owned and are never overwritten by later stack applies.

Components may instead configure `build_spec_path` in the Resource Manager applications JSON. An explicit path can be shared, for example `java/java-build-pipeline.yaml`. Resource Manager creates the file and parent folders from the default template only when missing, giving the DevOps engineer a working base. The path becomes user-owned after that first commit and is never refreshed or overwritten.

The build specs should stay readable and macro-oriented. Detailed branching, registry checks, chart parsing, image promotion, and release input resolution belong in `script/*.sh`.

Default pipeline names:

- `${component_name}-build`
- `${component_name}-pr`
%{ if delivery_enabled ~}
- `${application_name}-package`
- `${component_name}-release-build`
%{ endif ~}
