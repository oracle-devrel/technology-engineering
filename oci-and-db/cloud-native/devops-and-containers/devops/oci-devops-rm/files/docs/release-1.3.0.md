# OKE DevOps Starter 1.3.0

## Configurable Environment Names

Name the development, staging and production application environments, and the
non-production and production cluster targets. Generated pipeline names,
bootstrap stages, Helm values, labels and cluster-admin paths use those names.
Workflow roles, production approvals and immutable image promotion are unchanged.

The Customize environment names checkbox shows or hides all five naming inputs.
Defaults remain dev, staging, prod, noprod and prod. Saving the Console form with
customization disabled restores those defaults.

## Graphical Application Configuration

Applications and Components now use separate graphical lists. Applications hold
shared namespace and chart settings; each component references its application
by name and can specify a build path and initial chart version. This avoids
Resource Manager's nested-list data loss and blocked navigation. The legacy
application configuration field has been removed.

Application references, globally unique component names, safe paths, chart
versions, environment names and generated Helm release identities are enforced
by Terraform.

## Release Assets

- `stack.zip`: Resource Manager configuration in release mode.
- `stack.zip.sha256`: SHA-256 checksum for the stack archive.
- `oke-devops-starter.zip`: portable agent skill with custom-name awareness.
