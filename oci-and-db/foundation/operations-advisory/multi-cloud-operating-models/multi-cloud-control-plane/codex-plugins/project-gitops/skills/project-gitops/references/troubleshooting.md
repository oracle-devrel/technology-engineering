# Troubleshooting

## Read-only investigation

An investigation request authorizes evidence reads. Start with the selected project, PR or run, the failed stage and its revision. For a current PR, match evidence to the current head; for post-merge execution, match the configured push workflow to the merge commit. Label an explicitly requested historical run as historical. An older failure does not establish that the current revision fails. Missing or inaccessible evidence stays unverified.

Report the observed failure with its GitHub link, distinguish confirmed facts from hypotheses, and state the next step. A secret-resolution error identifies a native reference or required runtime binding; it does not prove current existence, permissions, or values. Diagnosis needs no CRQ or confirmation. Apply the failure table below as next-step guidance; it does not authorize a write. A correction requires its own semantic preview and fresh standalone confirmation before any GitHub write. Human review and merge remain mandatory.

| Failure | Tell the user |
| --- | --- |
| Template/catalog unavailable | Stop and ask the platform team to restore the approved source. |
| Branch or open PR already exists | Stop and provide its URL; reuse or close it through the Project Team's normal GitHub process, never create a suffixed duplicate. |
| Pull-request workflow is not found | Inspect recent branch runs without a `pull_request` event filter; protected project workflows use `pull_request_target`. |
| Pull-request workflow fails | Report the matching workflow evidence and identify whether the next step belongs to the project manifest or its owning platform contract. If the user requests a candidate-manifest correction, retain the exact branch and existing PR, regenerate the semantic preview, require fresh confirmation, then publish the correction to that branch. Never create a duplicate PR. |
| Missing or invalid handoff | Ask Cloud Operations to correct the environment handoff. |
| Vault reference or runtime-token failure | Report the failed reference or exact binding name and repository/cloud/environment/region from the candidate and workflow evidence. For OCI ADB, confirm the catalog uses `admin_password_secret_id` with a distinct secret OCID per database, in the deployment region and approved project/environment scope. Direct Project Team to check the current version and Cloud Operations to check scoped runner IAM and any runtime binding. State the published OCI ADB password policy without reading or testing its value. If prerequisites were absent from the preview, correct the preparation before another PR. Never request, read, print, set, or reconstruct secret values, query OCI, or fall back to GitHub Secrets. |
| All-ADB lifecycle request | When the request explicitly names `start` or `stop all OCI ADBs`, repository, environment, and region, enumerate the selected regional manifest and show every resulting display name in the preview. For any other group selector, ask for exact display names. |
| Inventory details unavailable | Report only the repository, environment, region, type, display name, and size available from committed regional manifests. Do not add paths, lifecycle commentary, or a disclaimer. |
| Preview drift | Regenerate the preview and request a new confirmation. |
