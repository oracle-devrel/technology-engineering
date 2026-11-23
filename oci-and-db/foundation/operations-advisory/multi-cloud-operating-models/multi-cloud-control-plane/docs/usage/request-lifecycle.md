# Request lifecycle

These rules apply whether you use the GitHub interface, optional UI, or optional Codex plugin.

## Before you begin

Confirm that you have write access to the handed-off `nonprod-<project>` or `prod-<project>` repository. OCI and Google Cloud requests use their approved foundation references in `environments/<environment>/environment_information.md`. Azure uses the resource request or relevant existing JSON and a runner already configured by Cloud Operations. Its Markdown section is optional context; no separate Azure handoff PR is required.

For Azure ADB, select a Small, Medium, or Large capacity profile, then choose its private or public mTLS variant. The published profiles use 2 ECPUs / 1 TB, 4 ECPUs / 2 TB, and 8 ECPUs / 4 TB respectively. Keep the template values unchanged. CPU auto-scaling remains enabled and storage auto-scaling is disabled by the official Azure module. Private requests require existing approved VNet and delegated-subnet references. Public requests require the resource group, region and dedicated native secret OCID; leave unused network references out of the request. The runner supplies the subscription and authentication through its existing `ARM_*` configuration, outside the resource JSON. A public endpoint accepts connections from any IP with mTLS and database authentication, so state that exposure explicitly before approval. Both connectivity variants use the same regional database manifest. Cloud Operations must install and pin the connectivity-aware Azure adapter before public requests are available.

Check that the request appears in [Reference capabilities](../reference/support.md).

Record a change reference such as `CRQ1234` in the pull request before review. The optional UI and Codex plugin require `CRQ` followed by 1 to 20 digits before preparing a Git change. For changes made directly in GitHub, follow your organization's change-reference requirements. The workflows do not validate the reference.

## Prepare the request

1. Choose a resource template from the installed [resource catalog](../../repository-sources/gitops-templates/resources-catalog/README.md) or a lifecycle template from the [operation catalog](../../repository-sources/gitops-templates/operations-catalog/README.md).
2. Change exactly one cloud, environment, and region in each pull request.
3. Use the selected OCI/Google handoff for foundation references. For Azure, use explicit request values or the relevant existing resource JSON; optional Markdown values are suggestions. Ask for missing or conflicting inputs and never invent references. A new ADB needs its own secret.
4. Use the secret reference defined by the catalog. Each OCI ADB needs its own Vault secret OCID in `admin_password_secret_id`, within the approved project/environment and deployment region. Google Cloud ADB uses its provider-native secret reference. Azure ADB also uses `admin_password_secret_id`, with one OCI Vault secret OCID per database in its approved project/environment scope. Its OCI region must match the trusted environment handoff; there is no binding name or separate region input. In Codex, [Project Team can prepare a missing secret through the skill](codex-plugin.md) with a separate confirmation and native Vault generation; the skill inserts its OCID before the GitHub proposal. The optional UI requires an existing OCID. The Project Team owns secret preparation and rotation; never put a value in Git or chat.
5. For a resource request, merge the catalog entry into the existing regional file. Replace `{}` for the first entry; do not create another file for the same configuration group, because Terraform does not deep-merge repeated root values. [Manifest paths](#manifest-paths) lists the file for each request.
6. Render every placeholder and validate the edited JSON before opening the pull request. Azure and Google VM SSH public keys are written directly into the manifest; never include a private key.

OCI project network security groups (NSGs) must exist before an OCI Compute request refers to their names. The NSG template contains optional ingress and egress TCP rule patterns for a new or existing project NSG. State the source or destination, its type, and destination-port range explicitly. The template sets the catalog protocol value itself. A public ingress source (`0.0.0.0/0`) is allowed only when the request explicitly requires it; the pull-request preview and review must identify that exposure.

## Review and execute

1. Create a focused branch and open a pull request.
2. Review the Terraform plan or Ansible check for only the intended change.
3. Obtain the required human approval.
4. Merge through the governed process.
5. Verify the post-merge workflow and cloud outcome.

Project Teams never receive deployment credentials. The trusted runner applies the merged change with its managed cloud identity.

When the request comes through Project GitOps, the assistant automatically follows the PR's current checks and returns a decision summary: declared configuration, additions, changes, deletions, replacements, affected resources and differences from the request, with review and merge readiness. It uses the trusted resource-action comment for the matching commit, workflow run and attempt; secret values stay outside the report. Declared settings are not proof of resolved cloud values. Missing matching evidence is reported as unverified. Lifecycle requests report validated targets and actions without a Terraform plan. Independent human review and an explicit human merge decision remain required.

In Codex, after reading the summary and obtaining independent approval for the current head in GitHub, Project Team may explicitly ask the skill to merge that exact PR. The skill rechecks its reviewed version, base, validation and repository restrictions before performing a guarded merge, then monitors the workflow for the actual merge commit. Changed evidence or a blocker stops the merge; the skill never approves, bypasses controls or schedules an automatic future merge. The optional UI does not offer this exception. See the [Codex plugin flow](codex-plugin.md).

## What a reviewer checks

On the supplied GitHub Free profile the approval is procedural, so this review is the governance boundary. Before approving, confirm that:

- the pull request changes exactly one cloud, environment, and region;
- foundation references match the OCI/Google handoff or, for Azure, the intended existing foundation supplied in the request or resource JSON;
- every NSG rule uses the approved catalog shape and its source or destination, TCP port range are the intended ones; any `0.0.0.0/0` ingress is explicitly approved as public exposure;
- the diff contains no passwords or private keys, each OCI or Azure ADB uses its own approved Vault secret OCID, and no placeholders remain;
- the Terraform plan or Ansible check shows only the intended change, and it ran against the current head commit;
- the change reference is recorded, if your change process requires one; and
- you are not the author of the change.

Reject the request rather than approving conditionally. The runner applies what was merged.

## Complete or remove a request

An operation file records one completed action; it is not desired state. After verifying the result, clear it using the route that created the request:

- For the GitHub interface, including cleanup after an optional-UI request, delete the lifecycle file in a focused pull request. The workflow accepts the removal and does not execute another operation.
- For an OCI lifecycle request created with the Codex plugin, delete the selected lifecycle file in its focused pull request.

Neither cleanup method reverses the completed operation.

To remove a resource, delete only the selected entry. If it is the final entry, replace the entire regional file with:

```json
{}
```

Confirm that the plan deletes only the intended resource. Never edit Terraform state manually or retry with a personal cloud account.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Missing or denied secret reference | Ask the Project Team to prepare the secret in its approved Vault scope and Cloud Operations to confirm runner access. Do not share the value. |
| Incomplete OCI/Google handoff value | Ask Cloud Operations to correct the environment handoff. |
| Missing Azure resource input | Supply the missing catalog input in the request or JSON; the Azure Markdown section is optional. |
| Operation target not found | Use the exact resource display name recorded in Terraform state. |
| Mixed environment or region rejected | Keep one cloud/environment/region tuple in the pull request. |
| Missing runner label | Ask Cloud Operations to correct the runner configuration. |
| Deployment failure | Retain the workflow link and safe diagnostic category, ask Cloud Operations to check the resource and state outcome, and submit a reviewed corrective change. Raw Terraform logs are private and removed after the job. |

## Manifest paths

| Request | Location |
| --- | --- |
| OCI project NSGs | `oci/{environment}/{region}/network/project-nsgs.json` |
| OCI Autonomous Database | `oci/{environment}/{region}/database/database.json` |
| OCI Compute | `oci/{environment}/{region}/compute/compute.json` |
| Azure private VM | `azure/{environment}/{region}/compute/compute.json` |
| Azure Autonomous Database | `azure/{environment}/{region}/database/database.json` |
| Google private VM | `gcp/{environment}/{region}/compute/compute.json` |
| Google Autonomous Database Serverless | `gcp/{environment}/{region}/workloads/adb.json` |
| OCI lifecycle operation | `oci/{environment}/{region}/lifecycle_operations/{operation}.json` |
