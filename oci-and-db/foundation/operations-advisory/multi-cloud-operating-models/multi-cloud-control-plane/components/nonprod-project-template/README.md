# Shared non-production project template

This template creates `nonprod-<project>` repositories using the explicit
`shared-nonprod-v2` contract. This package is for initial installations and
does not support another repository layout.

Manifest paths are `<cloud>/<environment>/<region>/...`; handoffs are stored at
`environments/<environment>/environment_information.md`. Allowed environments
are lowercase `dev`, `test`, and `uat`. Production aliases are permanently
rejected. The protected default branch owns `control-plane.json`, workflows,
and CODEOWNERS. Project changes may contain one cloud/environment/region tuple.

Configure one GitHub Environment per allowed environment with a scoped
`READINESS_MARKER` readiness secret (created separately in each GitHub
Environment) and environment-scoped
placeholder secrets. Do not use `secrets: inherit`.
