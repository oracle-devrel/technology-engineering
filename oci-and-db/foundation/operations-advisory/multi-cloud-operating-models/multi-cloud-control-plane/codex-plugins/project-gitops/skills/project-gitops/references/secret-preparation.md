# Project Team ADB secret preparation — Codex only

Use this procedure when Project Team requests an OCI or Azure ADB in Codex without its native secret OCID. Offer to prepare the secret and carry its OCID into the ADB JSON. If an OCID is supplied, keep the normal [setup](setup.md#native-secret-prerequisites) flow without creating a secret. The web UI keeps that flow and must ask for an existing OCID; never use the server's identity or credentials for this procedure.

This exception permits only `oci vault secret list`, `oci vault secret get` and `oci vault secret create-base64`, with the explicit scope below. Use the existing OCI CLI directly, not a generated script or executable. Do not retrieve secret bundles, generate a password locally, read credential/config/token files, use debug logging, rotate, update, delete or move secrets, create Vaults or keys, change IAM, or deploy an ADB. CloudOps provides the foundation and access; Project Team runs this preparation with its own authorized OCI profile. Local credentials remain with OCI CLI. Do not switch to the runner identity or a CloudOps administrative profile to bypass a denied request.

## Resolve and preview

1. Resolve the repository, ADB catalog inputs, environment, database key and CRQ through the normal workflow. Check the stable branch/PR collision and other request prerequisites before creating a secret. For a correction, keep the existing PR and branch. Read `environments/<environment>/environment_information.md` at a recorded current `main` commit, never from a request branch. Require handoff schema 5 for the exact project and environment, with an OCI region and complete `Vault`, `Vault key`, `Secrets compartment` and `DB compartment` references. The two compartments must match. Missing or ambiguous references go back to CloudOps; do not infer or repair them. Do not duplicate the Platform CI validator in the skill.
2. Use the Project Team profile and authentication method already specified in the conversation. If either is missing, ask for the profile name and method, not credentials. Do not hard-code a demo profile or launch login automatically. Authentication and permission errors stop preparation; ask Project Team to authenticate separately or CloudOps to check access.
3. Use the requested secret name, otherwise propose `<project>-<environment>-<cloud>-<adb-key>-admin`, with the handoff project name and target cloud (`oci` or `azure`). If it is not a valid OCI secret name, ask for a valid name rather than silently changing it. Each ADB needs a different secret. Azure deployment location never selects the secret's OCI region.
4. List the exact name in the handed-off Vault and secrets compartment, including all pages. Query errors are not absence. Inspect only metadata and require each returned name to equal the proposed name. If a secret is found, get its metadata and require `id` to equal the requested OCID and `name` to equal the previewed secret name, with the exact Vault, key, compartment and OCI region from the handoff, plus `ACTIVE`. Reject ambiguous results or incompatible identity/scope/state. Check its OCID against the project's committed OCI/Azure ADB declarations and current candidate; stop if assigned to another ADB. A matching name alone does not establish that a secret belongs to this database. Present reuse for confirmation instead of creating or overwriting it. A missing match permits proposing creation, not yet executing it.
5. Show one concise English preview: repository, project, environment, target cloud/ADB, secret name, OCI region, Vault/key/compartment references, profile and authentication method, CRQ, and `Create` or `Reuse`. State `GitHub writes: none`. For creation, explain that OCI generates the password inside Vault and the secret remains if the ADB request is abandoned. Ask `Do you confirm this secret preparation? Reply "confirm".` Only a standalone case-insensitive `confirm` after this preview authorizes the exact preparation. It does not authorize GitHub writes. Read-only metadata checks need no confirmation.
6. Before mutation, re-read current `main` and the handoff. If the preparation or handoff changed, discard confirmation and preview again. If only unrelated content on `main` changed, refresh the recorded revision and continue the same preparation. Recheck the name and reuse eligibility; a new collision changes `Create` to `Reuse` and requires a fresh preview. Do not change scope, name or identity under an earlier confirmation.

## OCI CLI commands

Set the following shell variables only to the resolved non-secret identifiers, profile name and authentication method: `ADB_OCI_PROFILE`, `ADB_OCI_AUTH`, `ADB_SECRET_REGION`, `ADB_SECRET_COMPARTMENT_OCID`, `ADB_SECRET_VAULT_OCID`, `ADB_SECRET_KEY_OCID`, `ADB_SECRET_NAME`. Check that all are nonempty and contain no unresolved placeholders before calling OCI. Do not ask the user to copy handoff OCIDs. Quote every variable, and use structural JSON rendering for CLI filters or manifest updates.

Read-only exact-name lookup; keep all states so a pending or failed secret is not mistaken for an unused name:

```bash
oci vault secret list \
  --profile "$ADB_OCI_PROFILE" --auth "$ADB_OCI_AUTH" \
  --region "$ADB_SECRET_REGION" \
  --compartment-id "$ADB_SECRET_COMPARTMENT_OCID" \
  --vault-id "$ADB_SECRET_VAULT_OCID" --name "$ADB_SECRET_NAME" --all \
  --query 'data[].{id:id,name:"secret-name",state:"lifecycle-state"}' --output json
```

For an existing or newly returned OCID in `ADB_SECRET_OCID`, read metadata and compare the scope and usable state before carrying it into the manifest:

```bash
oci vault secret get \
  --profile "$ADB_OCI_PROFILE" --auth "$ADB_OCI_AUTH" \
  --region "$ADB_SECRET_REGION" --secret-id "$ADB_SECRET_OCID" \
  --query 'data.{id:id,name:"secret-name",state:"lifecycle-state",compartment:"compartment-id",vault:"vault-id",key:"key-id"}' \
  --output json
```

Execute creation only after the preparation confirmation and fresh checks:

```bash
oci vault secret create-base64 \
  --profile "$ADB_OCI_PROFILE" --auth "$ADB_OCI_AUTH" \
  --region "$ADB_SECRET_REGION" \
  --compartment-id "$ADB_SECRET_COMPARTMENT_OCID" \
  --vault-id "$ADB_SECRET_VAULT_OCID" --key-id "$ADB_SECRET_KEY_OCID" \
  --secret-name "$ADB_SECRET_NAME" \
  --enable-auto-generation true \
  --secret-generation-context '{"generationType":"PASSPHRASE","generationTemplate":"DBAAS_DEFAULT_PASSWORD","passphraseLength":24}' \
  --wait-for-state ACTIVE --max-wait-seconds 300 --no-retry \
  --query 'data.{id:id,name:"secret-name",state:"lifecycle-state"}' --output json
```

These commands use [OCI native secret generation](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/vault/secret/create-base64.html), [metadata lookup](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/vault/secret/get.html) and [paginated name lookup](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/vault/secret/list.html). Do not claim that metadata checks establish password contents or the runner's permissions.

## Continue or recover

After confirmed creation or reuse, require matching metadata and `ACTIVE`, including `id` equal to the returned or recorded OCID and `name` equal to the previewed name, then retain the OCID and name in the conversation as resource references. Insert only the OCID in the catalog's existing `admin_password_secret_id`. Do not add profile names, generation settings, passwords or extra binding fields to the manifest. Continue at the normal GitHub semantic preview with the real OCID and a separate standalone `confirm`. The JSON syntax, branch drift checks, independent human review and protected execution remain unchanged. Platform CI still performs its own complete validation against its trusted handoff.

If creation times out or its result is uncertain, do not repeat the create command. Use the returned OCID when available, otherwise repeat the exact-name metadata lookup. If exactly one matching secret is now `ACTIVE`, with the approved scope and no other declared ADB assignment, recover its OCID under the same preparation and continue. A response with a different OCID than the recorded creation, an ambiguous match, a query error, incompatible metadata, a non-ACTIVE state or no match leaves preparation unresolved: stop, report only the known metadata and next step, and keep the references for recovery. A later retry needs a fresh preview and confirmation after resolving the earlier outcome. Never add a suffix, overwrite, delete, or create another secret to obtain a successful take.

If GitHub publication subsequently fails or the user abandons the request, report the retained secret reference. Do not roll it back. A resumed request can propose reuse of that same secret after the metadata and declaration checks; do not create it again. Keep secret preparation separate from ADB deployment success.
