# Project infrastructure repository

Use this repository after the platform team has completed project onboarding.
It contains project workloads, project network security groups, and supported
lifecycle requests. It must not create OCI compartments, groups, policies, or
other foundation resources.

Read `enviroment_information.md` first. It records the approved project,
environment, compartments, VCN, subnets, and Landing Zone provenance. JSON
manifests remain the executable source; the handoff document is not parsed by
deployment workflows.

## Standard workflow

1. Choose an approved entry from `gitops-templates`.
2. Update the correct regional manifest on a focused branch.
3. Open a pull request and review the Terraform plan or Ansible check.
4. Obtain independent approval and merge.
5. Verify the workflow and cloud outcome.

## Manifest locations

| Request | Path |
|---|---|
| OCI project NSGs | `oci/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{region}/database/database.json` |
| OCI Compute | `oci/{region}/compute/compute.json` |
| OCI lifecycle operation | `oci/{region}/lifecycle_operations/{operation}.json` |
| Azure infrastructure | `azure/{region}/` |
| Google ADB-S | `gcp/{region}/workloads/adb.json` |

Keep each Terraform root configuration in one regional file. Terraform does
not deep-merge two variable files that define the same root key.

## Important boundaries

- Never commit passwords, keys, or cloud credentials. Keep secret placeholders
  such as `__ADB_ADMIN_PASSWORD__` in JSON and create the matching GitHub Actions
  secret.
- OCI project NSGs must be added to the single regional
  `project-nsgs.json` file before workloads reference their keys.
- Lifecycle manifests require `operation_type` and an exact Terraform-state
  display name for every target.
- OCI Autonomous Database start/stop and OCI Compute `deploy-agent` are the
  available Day 2 operations. Azure and Google Day 2 are not available.
- Do not modify shared workflow or orchestrator refs without platform approval.

The optional UI and Codex app assistant prepare the same pull requests. Neither
is required and neither deploys directly to a cloud.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
