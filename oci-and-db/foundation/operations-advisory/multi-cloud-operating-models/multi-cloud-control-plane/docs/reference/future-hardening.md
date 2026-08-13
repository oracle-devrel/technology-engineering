# Future paid-environment hardening

This document describes a future hardened release for organizations using a
GitHub plan that supports the required controls. It is not implemented by, or
selectable in, the GitHub Free MVP.

That release would use paired GitHub Environments for each logical
environment: `dev` and `dev-apply` (and the equivalent `test`, `uat`, and
`prod` pairs). Plan/check jobs would use the base Environment; apply/execute
jobs would use the apply Environment. The apply Environment would carry
required reviewers and prevention of self-review where supported. Its secret
set would be independently scoped and rotated.

The final installation would also protect `main`, require code-owner review
and passing checks, restrict administrators and direct pushes, and use
organization runner groups to isolate cloud and production identities. Exact
availability varies by GitHub plan and repository visibility, so it must be
verified against current GitHub documentation at deployment time.

Do not add these controls as an untested profile switch to this MVP. Deliver
them as a separate hardened release with its own installation instructions,
negative tests for secret and Environment isolation, and a complete
non-production end-to-end qualification.
