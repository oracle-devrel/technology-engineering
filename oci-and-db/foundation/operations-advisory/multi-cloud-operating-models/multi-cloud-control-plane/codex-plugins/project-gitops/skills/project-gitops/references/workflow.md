# Workflow

1. Identify the handed-off repository and, for non-production, ask the user to
   select `dev`, `test`, or `uat`.
2. Confirm the requested Day 1 resource is supported: OCI NSG, Compute, and
   ADB; Azure VM and ADB; Google Cloud VM and ADB-S. OCI ADB start and stop are
   the only supported Day 2 operations. Refuse Azure and Google Cloud Day 2.
3. For OCI workload networking, derive the private DB subnet for an ADB and
   the private App subnet for a VM from the environment handoff. Project NSGs
   are not handoff resources: inspect the base `network/project-nsgs.json`
   instead. An empty NSG list is valid for a private ADB or VM and uses the
   subnet security lists. If the user requests an NSG, require an explicit
   selection from existing project NSG keys; never invent a key. A new NSG is a
   separate request and manifest change that must merge before a VM or ADB can
   reference it.
4. For a new OCI Compute request, offer the approved Frankfurt
   `VM.Standard.A1.Flex` catalog image or ask for a regional image OCID. The
   user chooses manually. Do not resolve images through OCI CLI or a cloud API.
5. Create a disposable clone in a child directory named exactly as the canonical
   project repository. Create one `agent/<resource>-...` branch from exact
   `origin/main`.
6. Edit one canonical manifest path. Use the environment handoff. OCI uses TBAC
   Application for Compute, Database for ADB and lifecycle, and Infrastructure
   for NSGs.
7. Run the packaged validator after the edit:

   ```bash
   python3 scripts/validate-change.py \
     --repo <project-repository> \
     --base-ref origin/main
   ```

   Run it again with `--expect-base-sha` and `--expect-content-sha256` after
   confirmation.
8. Use the returned semantic summary to prepare the single user preview.
9. Accept only the user's exact `Confirm` reply. After confirmation and revalidation, stage only the validated path, commit,
   push, and conditionally create one pull request. Stop before merge.

Use `{}` only to clear a completed OCI ADB lifecycle request. Do not use it for
another resource change. A validated change contains one VM or NSG, or up to
three OCI ADB mutations.
