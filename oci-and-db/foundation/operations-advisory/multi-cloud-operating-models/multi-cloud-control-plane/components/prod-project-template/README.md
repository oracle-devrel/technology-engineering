# Production project template

This template creates one `prod-<project>` repository under the explicit
`production-v1` contract. Production is separate from shared non-production;
it uses only the `prod` GitHub Environment, production-isolated runners and
production approvers. Manifest paths are `<cloud>/prod/<region>/...` and the
handoff is `environments/prod/environment_information.md`.

Replace `__PROJECT__` and the CODEOWNERS team before granting project access.
Configure `READINESS_MARKER` and workload placeholder secrets only in the
`prod` GitHub Environment. Require independent production approval and passing
checks; do not use `secrets: inherit`.
