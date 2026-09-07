# Application Delivery

## Pull Requests And Builds

1. Create a component feature branch and open a PR to `main`.
2. Confirm the component PR pipeline runs the repository-owned build spec.
3. Merge only after validation succeeds.
4. Confirm the main build publishes exactly one immutable seven-character Git
   SHA image tag.
5. In `oci_devops` mode, confirm the component dev pipeline deploys that tag.
   In `build_only` mode, stop after image publication.

The seeded PR specification is intentionally a placeholder because tests depend
on the component language and integration boundaries. The main build expects a
multi-stage `Dockerfile` to own language-specific compilation.

## Release Promotion

Run `<component>-release-build` with a strict semantic RC tag such as
`1.0.0-rc.1` and, when needed, an explicit commit.

Verify that the pipeline:

1. Finds the SHA7 image for the selected commit.
2. Creates the RC Git tag and retags the same image digest with Skopeo.
3. Triggers `<component>-release`.
4. Deploys the RC to staging.
5. Pauses for production approval.
6. Retags the approved RC image to the final version.
7. Deploys the final image to production.
8. Records Helm status and tags the released commit with the final version.

Treat image digest equality, Helm release state, and Git tags as separate
evidence. A failure in the final informational status stage does not undo a
successful production deployment.

## Application Bootstrap And Baseline

Run `<application>-bootstrap` to create the application namespace and OCIR pull
secret in pre-production and production. The two cluster stages are independent
and may run in parallel or individually.

Package and deploy the umbrella chart separately from component charts. It owns
shared namespace resources and keeps component subcharts disabled. Confirm the
pre-production baseline before approving production.

When pre-production and production select the same physical cluster, expect
application releases to remain distinct by Helm release name. Treat this as an
evaluation configuration rather than production isolation.
