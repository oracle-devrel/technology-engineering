# Declared resource inventory

Read the target project at `main` and list resources from the committed manifests in the selected scope. This query needs no CRQ, confirmation, branch or PR. Render this compact format:

```markdown
## Resource inventory

Repository: `<repository>`
Environment: `<environment>`
Region: `<region>`

| Type | Display name | Size |
| --- | --- | --- |
| `<resource type>` | `<display name>` | `<size>` |
```

Use `Small`, `Medium` or `Large` for OCI Compute, OCI ADB and Azure ADB when the declaration matches one published profile for that resource. Compare the fixed profile settings in the selected catalog template, including the applicable Azure private or public mTLS variant. Allow documented input substitutions and apply documented defaults where the declaration omits those fields. Use `N/A` for a missing, ambiguous or unverified match and for resource types without a published size profile.

Keep the inventory to the scope and table above. Omit manifest paths, lifecycle status and deployment commentary.
