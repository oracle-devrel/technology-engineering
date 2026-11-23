# Troubleshooting

## Read-only investigation

An investigation request authorizes evidence reads. Start with the selected project, PR or run, the failed stage and its revision. For a current PR, match evidence to the current head; for post-merge execution, match the configured push workflow to the merge commit. Label an explicitly requested historical run as historical. An older failure does not establish that the current revision fails. Missing or inaccessible evidence stays unverified.

Report the observed failure with its GitHub link, distinguish confirmed facts from hypotheses, and state the next step. A secret-resolution error identifies a native reference; it does not prove current existence, permissions, or values. Diagnosis needs no CRQ or confirmation. Apply the failure table below as next-step guidance; it does not authorize a write. Publishing a correction requires its own semantic preview and fresh standalone confirmation. Independent human review and an explicit merge decision remain mandatory; an exact Codex merge instruction follows [PR merge](pr-merge.md).

| Failure | Tell the user |
| --- | --- |
| Template/catalog unavailable | Stop and ask the platform team to restore the approved source. |
| Branch or open PR already exists | Stop and provide its URL; reuse or close it through the Project Team's normal GitHub process, never create a suffixed duplicate. |
| Pull-request workflow is not found | Inspect recent branch runs without a `pull_request` event filter; protected project workflows use `pull_request_target`. |
| Pull-request workflow fails | Report the matching workflow evidence and identify whether the next step belongs to the project manifest or its owning platform contract. If the user requests a candidate-manifest correction, retain the exact branch and existing PR, regenerate the semantic preview, require fresh confirmation, then publish the correction to that branch. Never create a duplicate PR. |
| Missing or invalid OCI/Google handoff | Ask Cloud Operations to correct the environment handoff. |
| Missing Azure resource inputs | Use the explicit request or relevant existing JSON; ask only for missing or conflicting inputs. The Azure Markdown section is optional. |
| Azure authentication or subscription failure | Direct Cloud Operations to check the runner configuration using the matching workflow evidence. Do not request credentials or add a handoff PR. |
| Vault reference failure | Use the reference and prerequisites in [setup](setup.md#native-secret-prerequisites). Direct Project Team to check its current version and Cloud Operations to check runner IAM. Do not read or reconstruct values, register a binding, or fall back to GitHub Secrets. The Codex [secret-preparation procedure](secret-preparation.md) is the only permitted cloud exception; it does not authorize general cloud diagnosis or replacement of a failing secret. Correct an incomplete preview before proposing another write. |
| Missing ADB secret | In Codex, offer [Project Team secret preparation](secret-preparation.md). In the web UI, ask for an existing OCID. Never obtain host credentials or use the runner identity. |
| Secret creation timeout or uncertain result | Follow the preparation recovery procedure: query metadata before any retry, recover the same ACTIVE secret when its identity and scope are established, otherwise stop with the outcome unresolved. Do not overwrite, suffix the name or create another secret. |
| Unresolved placeholder | Render the selected catalog's inputs before publishing. Public SSH keys are literal public inputs; password tokens and runtime bindings are unsupported. |
| Terraform diagnostic category | Report the fixed category as a possible cause, with the matching workflow link and failed stage. Do not infer a definitive root cause or retrieve raw logs; Cloud Operations owns cloud and state investigation. |
| All-ADB lifecycle request | When the request explicitly names `start` or `stop all OCI ADBs`, repository, environment, and region, enumerate the selected regional manifest and show every resulting display name in the preview. For any other group selector, ask for exact display names. |
| Inventory details unavailable | Report only the repository, environment, region, type, display name, and size available from committed regional manifests. Do not add paths, lifecycle commentary, or a disclaimer. |
| Preview drift | Regenerate the preview and request a new confirmation. |
| Merge requested before review or evidence is ready | Report the exact missing current-head approval, check or matching safe plan/check. Do not approve, merge, enable auto-merge or wait to merge later automatically. |
| Reviewed PR head, base or validation attempt changed | Refresh the decision summary and obtain a new explicit merge instruction. Do not merge the newly observed version under the earlier instruction. |
| Merge rejected, denied or outcome uncertain | Read the exact PR state. Report a verified existing merge and monitor its actual merge commit, or stop with the unresolved/blocking result. Do not retry blindly, bypass restrictions, change merge method, enqueue, reopen or update the branch. |
