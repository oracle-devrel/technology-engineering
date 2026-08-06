# Platform CI

These reusable GitHub Actions workflows run reviewed project changes. Project
repositories call them for Terraform plan/apply and supported Ansible checks or
operations.

Project workflows call the organization's protected `platform-ci` `main`
branch directly. GitHub grants the temporary scoped token required to download
the private reusable workflow and composite actions; no deploy key or personal
access token is required. The deployment runbook records the initial Platform
CI commit as installation evidence and pins each cloud orchestrator to its
approved immutable revision.

## Required runner

Use a trusted Linux self-hosted runner with:

- Git, `jq`, `rg`, and Python 3.11 or later.
- Outbound HTTPS access to install the pinned Terraform 1.12.1 runtime.
- OCI Instance Principal access to the Object Storage state bucket.
- `STATE_NAMESPACE`, `STATE_REGION`, and
  `OCI_CLI_AUTH=instance_principal` in the runner environment.
- The target-cloud authentication required by each enabled profile.

Azure additionally needs Azure CLI and `ARM_CLIENT_ID`, `ARM_CLIENT_SECRET`,
`ARM_TENANT_ID`, and `ARM_SUBSCRIPTION_ID`. Google needs
`GOOGLE_CREDENTIALS`, `GOOGLE_APPLICATION_CREDENTIALS`, or Application Default
Credentials. Keep all credential values outside Git.

## Terraform workflow

`.github/workflows/terraform-shared.yaml` accepts the mode, cloud, region,
environment, validated manifest ref, orchestrator repository and immutable ref,
state bucket, readiness marker, runner labels, and one explicit secret bundle.

- Pull requests run validation and plan and report the result for review.
- Merges to `main` create and apply a saved plan on the trusted runner.
- The region normally comes from the changed
  `{cloud}/{environment}/{region}/` path.
- State is isolated by GitHub repository, cloud, environment, and region in
  OCI Object Storage.

Before Terraform runs, JSON files are copied to the runner's temporary
directory. Environment-qualified tokens such as
`__DEV_ADB_ADMIN_PASSWORD__` resolve only from the explicitly passed JSON
repository secret bundle. The workflow rejects unqualified, cross-environment,
or unresolved tokens and never modifies the checked-out manifest. It masks
each decoded value before Terraform can emit it.

Terraform does not deep-merge repeated root variables. Keep each root
configuration in one regional file, including OCI project NSGs in
`oci/{environment}/{region}/network/project-nsgs.json` and Google ADB-S
resources in `gcp/{environment}/{region}/workloads/adb.json`.

## Ansible workflow

`.github/workflows/ansible-shared.yaml` runs check mode on pull requests and
executes after approval and merge. Current end-to-end operations are:

- OCI Autonomous Database start or stop.
- OCI Compute `deploy-agent` over SSH.

Operation manifests belong under
`oci/{environment}/{region}/lifecycle_operations/{operation}.json`. Operations
must resolve an exact display name in Terraform state. Azure and Google Day 2
are not available.

## Operation playbook structure

The execution action maps each validated `operation_type` to one supported
operation playbook. There is no aggregate master playbook and no dynamic file
path from a project manifest. Each operation playbook is a small facade over
the same explicit phases:

```text
operation playbook
├── precheck — read and validate the target before a change
├── apply    — run only after merge with execution mode `execute`
└── verify   — read back and report the result
```

Common tasks live under `ansible/playbooks/common/oci/<operation>/`. Add a new
operation only through the extension model: catalog and manifest validation,
inventory extraction, an allow-listed action mapping, these phases, and
qualification evidence. Do not add a generic task runner or accept a playbook
path from project input.

For `deploy-agent`, the default SSH user is `opc` and the default private key is
`/home/github-runner/.ssh/oci_vm_key`. OP03 creates and protects this key for
the `github-runner` service account; project repositories never contain it.
Override the defaults with
`COMPUTE_ANSIBLE_USER` and `COMPUTE_SSH_PRIVATE_KEY_FILE` on the runner. Verify
SSH host trust and protect the private key.

## Project boundary

Project repositories contain workloads, project NSGs, and supported operation
manifests only. OCI compartments, groups, and IAM policies are created before
handoff and must not be recreated from a project repository.

## License

Copyright (c) 2026 Oracle and/or its affiliates. Licensed under the Universal
Permissive License, Version 1.0. See [LICENSE](LICENSE).
