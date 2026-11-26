# Request lifecycle

Follow these steps with GitHub, the optional UI or the optional Codex plugin. Each route opens the same kind of pull request and uses the same review and execution process.

## Before you begin

Use a handed-off project repository where you have write access. Check that the resource or operation is [supported](../reference/support.md). Choose one cloud, environment and region for the pull request.

A resource pull request can change several supported resource entries in that scope. An OCI operation needs its own pull request with exactly one operation file; that file can name several supported targets in the same scope. Keep resource changes and operations separate. For example, creating a database and stopping another database in OCI `dev` and `eu-frankfurt-1` requires two pull requests: one resource request and one `adb-lifecycle.json` operation request.

Use the approved OCI or Google Cloud references in `environments/<environment>/environment_information.md`. For Azure, use the existing foundation inputs in the request or resource JSON. The Azure notes in the handoff can suggest values. Cloud Operations sets the subscription and authentication on the runner.

Record your organization's change reference before review. The UI and Codex require `CRQ` followed by 1 to 20 digits before preparing a Git change. GitHub workflows check the manifest. Your organization's process governs change references for direct GitHub requests.

## Prepare the request

1. Select a [resource](../../repository-sources/gitops-templates/resources-catalog/README.md) or [operation template](../../repository-sources/gitops-templates/operations-catalog/README.md) from the approved catalog.
2. Supply the approved foundation details. For OCI and Azure Autonomous Database (ADB), use one dedicated Vault secret OCID per database in `admin_password_secret_id`. Google Cloud ADB uses its provider-native reference. See [secret delivery](../reference/security.md#secret-delivery) and [Codex secret preparation](codex-plugin.md#prepare-and-publish).
3. Add a resource entry to the existing file for that configuration group and region. Replace `{}` for its first entry. Terraform expects each root configuration in one file. For an operation, use the path from the operations catalog and the exact target name from Terraform state.
4. Replace all placeholders and validate the JSON before opening the pull request. Use only approved SSH public keys where required. Keep passwords and private keys out of the request.

For an OCI network security group (NSG) rule, supply the TCP source or destination, its type and the destination-port range. The template supplies the protocol. Review any explicitly requested public ingress (`0.0.0.0/0`). OCI Compute must reference an existing project NSG key. See the [OCI network template](../../repository-sources/gitops-templates/resources-catalog/README.md#oci--network).

For Azure ADB, choose a catalog size and connectivity option. The public mTLS option permits connections from any IP with a wallet and database authentication. State that exposure in the request. The [Azure catalog](../../repository-sources/gitops-templates/resources-catalog/README.md#azure--databases) lists the inputs and adapter prerequisite.

## Review and execute

1. Open a focused pull request and wait for the Terraform plan or Ansible check.
2. Give the current request and matching evidence to an independent human reviewer. Use the manifest diff for declared settings and the report for planned actions or validated targets.
3. After approval, merge through the approved process. GitHub is the standard route. See the [explicit Codex merge steps](codex-plugin.md#merge-and-verify) when using the plugin.
4. Open the workflow for the merge commit. Verify that the execution step succeeded and check the applicable cloud outcome. Keep the pull request and workflow as evidence. A green plan or check describes proposed work. The post-merge run records execution.

## What a reviewer checks

| Check | Before approving |
| --- | --- |
| Scope and inputs | Confirm one cloud, environment and region. Check the foundation inputs against the handoff or the intended Azure foundation. |
| Exposure and secrets | Check approved network rules and any requested public access. Check dedicated database secret references and confirm that credentials and placeholders are absent. |
| Expected change | Read the matching plan or check for the current pull request revision. Confirm every affected resource or operation is intended. |
| Approval | Confirm the required change reference and that you are independent of the author. Follow the [controls for your GitHub plan](../reference/security.md#github-plan-controls). |

Ask for a correction if any check fails. Review the updated request and its current evidence before approving.

## Complete or remove a request

| Goal | What to change |
| --- | --- |
| Clear a completed operation | After verifying the result, remove the completed lifecycle file in a focused pull request. This closes the recorded request and leaves the resource in its current state. The Codex plugin can prepare the clear request. |
| Remove a resource | Delete only its entry from the regional file. If it was the last entry, replace the file content with `{}`. Check that the plan deletes only the intended resource. |

If removal fails, use the reviewed correction process and keep Terraform state under Cloud Operations control.

## Troubleshooting

| Problem | Action |
| --- | --- |
| Missing or denied secret reference | Project Team checks the reference in its approved Vault scope. Cloud Operations checks runner access. |
| Missing foundation input | Cloud Operations corrects the OCI or Google Cloud handoff. For Azure, supply the intended value in the request or resource JSON. |
| Operation target missing | Use the exact display name recorded in Terraform state. |
| Mixed scope or missing runner | Keep one cloud, environment and region per pull request. Ask Cloud Operations to check the runner labels for that scope. |
| Deployment failure | Share the workflow link and safe diagnostic category with Cloud Operations. Verify the resource and state outcome before opening a reviewed correction. |

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
