# Troubleshooting

| Failure | Tell the user |
| --- | --- |
| Template/catalog unavailable | Stop and ask the platform team to restore the approved source. |
| Branch or open PR already exists | Stop and provide its URL; reuse or close it through the Project Team's normal GitHub process, never create a suffixed duplicate. |
| Pull-request workflow is not found | Inspect recent branch runs without a `pull_request` event filter; protected project workflows use `pull_request_target`. |
| Pull-request workflow fails | Use the workflow result; fix the template or manifest in the repository that owns the contract. |
| Missing or invalid handoff | Ask Cloud Operations to correct the environment handoff. |
| Secret placeholder failure | Report the exact environment bundle and member keys required by the tokens. If the bundle is new, provide one copy-paste-safe JSON object with only values as angle-bracket placeholders. If it already exists, provide only the missing member-key fragment and direct the administrator to merge it through the approved secret process without replacing existing members; the agent cannot read or reconstruct those values. For OCI ADB, first confirm that each database has a distinct database-scoped token and state the published password policy: 12 to 30 characters, uppercase, lowercase, digit, no double quote, and no `admin` substring. If the prerequisite or per-ADB token rule was absent from the preview, treat that as a preparation error to correct before another PR; never provide, read, or set values in chat or Git. |
| Ambiguous Day 2 target | Do not interpret `all`, `development`, a prefix, or a group as a target set. Ask for the exact display names, environment, and region. Platform CI verifies those names against Terraform state. |
| Deployed-resource inventory requested | Explain that the available inventory is `Declared resources (Git)`, not Terraform state. A deployed-state inventory requires a published read-only Platform CI workflow. |
| Preview drift | Regenerate the preview and request a new confirmation. |
