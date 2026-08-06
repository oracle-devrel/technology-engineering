# Operations

1. Parse `mccp-installation.json` with `jq -e`, reject unresolved placeholders,
   derive its canonical catalog repository/ref, then validate `gh`
   authentication, exact private repository metadata, canonical project
   repository name, and exact `main` SHA.
2. Resolve the validator-returned catalog repository through GitHub API at the
   validator-returned SHA, verify its blob hash, and include repository, commit,
   and blob SHA in the semantic preview.
3. For an explicit new OCI Compute request for Oracle Linux 9 on
   `VM.Standard.A1.Flex`, derive `APP_COMPARTMENT_ID` and `OCI_REGION` from the
   selected `environment_information.md` handoff, then run only this read-only
   command:

   ```bash
   image_json=$(oci compute image list \
     --compartment-id "$APP_COMPARTMENT_ID" \
     --region "$OCI_REGION" \
     --operating-system 'Oracle Linux' \
     --operating-system-version '9' \
     --shape 'VM.Standard.A1.Flex' \
     --lifecycle-state AVAILABLE \
     --sort-by TIMECREATED \
     --sort-order DESC \
     --limit 1 \
     --query 'data[0].{id:id,display_name:"display-name",operating_system:"operating-system",operating_system_version:"operating-system-version",time_created:"time-created"}')
   printf '%s\n' "$image_json"
   printf '%s\n' "$image_json" | jq -e \
     'type == "object" and (.id | type == "string" and length > 0) and (.display_name | type == "string" and length > 0) and .operating_system == "Oracle Linux" and .operating_system_version == "9" and (.time_created | type == "string" and length > 0)'
   ```

   Print the selected record before validation so its exact OCID remains
   available for the semantic preview. Require non-empty `id`, `display_name`, and
   `time_created`, and exact `Oracle Linux` / `9` metadata. Include that record
   and the exact OCID in the semantic preview, then write only the OCID to
   `platform_image.ocid`. Fail closed for no result or incomplete metadata.
4. Create a fresh disposable parent directory, then clone into its child named
   exactly `nonprod-<project>` or `prod-<project>` and create one
   collision-free branch from exact `origin/main`. The shared-layout validator
   rejects an arbitrary clone-directory name.
5. Edit one canonical aggregate manifest. For `nonprod-<project>`, first run
   `validate-shared-layout.py` for the explicitly selected `dev`, `test`, or
   `uat` environment; then run `validate-change.py` for both non-production and
   production repositories. Use only
   `{cloud}/{environment}/{region}/...` manifest paths and the matching
   `environments/<environment>/environment_information.md` handoff.
   For OCI, use the schema-3 TBAC target from that handoff: Application for
   Compute, Database for ADB and ADB lifecycle, and Infrastructure for project
   NSGs. A lifecycle manifest must include `database_compartment_id`. For OCI
   Compute, one validated change contains exactly one VM; use a separate change
   and pull request for each additional VM.
6. Show the semantic diff, destructive/replacement warnings, branch, base SHA, and content SHA-256; then stop for fresh confirmation.
7. Revalidate hashes, stage only the validated path, commit, push, and conditionally create one PR. Stop before merge.
8. After human merge, monitor only the configured exact workflow and merge commit. Report configuration and structured workflow results without inferring cloud state.

On interruption, discard stale confirmation and rebuild the preview from exact remote state.

Post-merge monitoring is continuous by default. Poll structured `gh run list` and `gh run view`
reads every 15–30 seconds until terminal. Treat missing, queued, pending, waiting, requested, and
in-progress states as progress, not a final answer. Keep the task active, report progress through
commentary only when status changes or about once per minute, and never require the user to return
and announce completion. Stop early only for an explicit one-time snapshot, user cancellation, or
repeated authentication/API failure.

Run commands directly and never generate helper executables. Status and monitoring use structured
reads without cloning or local files. Register cleanup when a writable temporary workspace is
created and remove it when the operation ends or is abandoned.
