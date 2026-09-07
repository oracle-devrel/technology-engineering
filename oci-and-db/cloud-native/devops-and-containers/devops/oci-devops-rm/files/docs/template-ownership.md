# Template Ownership And Upgrades

The stack bootstraps OCI DevOps resources and repositories, but it is not intended to remain authoritative for every user customization.

## Release Mode

`./update.sh` creates a release archive by default.

- Generated DevOps resources retain `ignore_changes = all` where the provider permits it.
- Teams can customize pipelines, stages, artifacts, tags, and repository settings without a later stack apply reverting them.
- Repository seed operations preserve existing paths and add only missing entity-specific content.
- A newer stack ZIP does not automatically upgrade customized pipeline internals or existing repository files.

Use release mode for distributed stacks that become starting points for developer and administrator ownership.

## Development Mode

Build a development archive with:

```bash
STACK_DEVELOPMENT_MODE=true ./update.sh
```

Development mode removes release-only lifecycle ignores from the staged archive and sets the hidden `development_mode` input. It lets the development Resource Manager stack refresh shared template resources while retaining provider-safety ignores and repository ownership protections.

Use development mode only for stack development and functional testing. It is not a general mechanism for forcing repository content over user changes.

## Repository Seeding

| Seed target | Later apply behavior |
| --- | --- |
| Shared `pipelines` files | Seed when empty; preserve existing files |
| Component source repository | Seed when empty; preserve developer content |
| Application baseline chart | Seed when empty |
| New component chart directory | Add only when the path is missing |
| New entity-specific pipeline specification | Add only when the path is missing |
| Explicit component `build_spec_path` | Add the default starter only when missing, creating parent folders automatically; never refresh the file afterward |
| `cluster-admin` repository | Add initial content without replacing existing paths |

Removing an application, component, or tool from Resource Manager may destroy Terraform-managed OCI resources, but it does not delete the corresponding Git files or live Kubernetes workloads automatically.

## Adopting A Template Upgrade

1. Read the newer stack release notes and identify affected Terraform resources, pipeline files, and scripts.
2. Back up or branch customized repositories.
3. Apply infrastructure-compatible changes through Resource Manager.
4. Compare newer repository templates with the user-owned files.
5. Port desired changes through normal pull requests instead of reseeding repositories.
6. Test one application/component or cluster target before broad adoption.
7. Verify custom OCI DevOps stage parameters and tags after the apply.

## Ownership Test

Before distributing a release archive:

1. Apply it once and customize a generated pipeline field.
2. Apply the same archive again.
3. Confirm the customization remains.
4. Add a new application or component and apply again.
5. Confirm only missing resources and repository paths are added.
