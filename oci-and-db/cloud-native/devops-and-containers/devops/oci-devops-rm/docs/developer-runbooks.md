# Developer Runbooks

These runbooks cover routine component work. Replace placeholders such as `<component>` and `<application>` with the names derived from the Resource Manager application configuration.

## Add A Component

Adding a component changes the stack topology and therefore requires the stack/platform owner.

1. Add a globally unique component name to the application's `components` list in Resource Manager.
2. Apply the stack. Terraform creates the missing repository, pipelines, artifacts, triggers, and chart path without replacing existing repository files.
3. Clone the new `<component>` repository and replace the seeded source with the component implementation.
4. Replace the placeholder PR build specification with language-specific tests.
5. Implement a multi-stage `Dockerfile` that produces the runtime image.
6. Review the seeded chart under `<application>-chart/<application>/charts/<component>`.
7. Open pull requests for source and chart changes. Do not commit directly to protected `main` branches.

Expected result: merging source to `main` builds `<component>:<sha7>` and deploys Helm release `<component>-dev`.

Before the first component deployment, run `<application>-bootstrap` with the OCIR username and Vault secret OCID. A full run initializes noprod and prod in parallel; use an OCI single-stage deployment for only one target. Publish and deploy the application baseline separately through `<application>-deploy`.

## Customize PR Validation

Edit `.oci-devops/pull-request-pipeline.yaml` in the component repository.

1. Keep tests independent of image publishing and deployment.
2. Install or invoke language-specific tooling inside the build specification.
3. Run unit tests first, then integration, contract, lint, or security checks as appropriate.
4. Make every failed check return a nonzero exit code.
5. Open or update a pull request and confirm `<component>-pr` is triggered.

The seeded `Unit tests succeeded` command is only a placeholder and is not a real quality gate.

## Change Component Runtime Code

1. Create a feature branch in `<component>`.
2. Commit the source and `Dockerfile` changes.
3. Open a pull request to `main` and make `<component>-pr` pass.
4. Merge using the configured repository strategy.
5. Confirm `<component>-build` creates only the 7-character SHA image tag.
6. Confirm `<component>-dev-deploy` updates release `<component>-dev` in the application namespace.

Do not manually create a version image tag during this workflow. Release tags are created by promotion.

## Change A Component Chart

1. Create a branch in `<application>-chart`.
2. Change only `<application>/charts/<component>/**`.
3. Increment the component chart version in its `Chart.yaml`.
4. Open and merge a pull request.
5. Confirm only `<component>-build` runs for this chart path.
6. Confirm it skips the image build, publishes the component chart, and redeploys `<component>-dev` with the latest source SHA image.

Do not increment the umbrella chart version for a component-only change.

## Promote A Release Candidate

1. Verify the desired commit has a successful main build and a corresponding `<sha7>` image.
2. Run `<component>-release-build` with `release_tag`, for example `1.2.0-rc.1`.
3. Optionally provide the full `commit_id`; otherwise the pipeline resolves current `main`.
4. Confirm the RC Git tag and image tag point to the selected commit and image digest.
5. Verify `<component>-staging` in the pre-prod cluster.
6. Review the successful staging deployment and approve production.
7. Confirm the production-only Helm status stage succeeds.
8. Confirm release `<component>`, final image `1.2.0`, and final Git tag `1.2.0` exist after production succeeds.

Never reuse an RC or final version for a different commit. Choose a new RC number or release version.

## Roll Back A Component

OCI DevOps retains the chart and values snapshot used by a deployment, even if the current artifact definition later changes.

1. Identify the last successful deployment with the desired chart, image tag, and values.
2. Use OCI DevOps rollback for the affected component deployment pipeline.
3. Verify the Helm release revision and workload image in the target namespace.
4. Confirm readiness and component health before closing the incident.
5. Fix forward through a new commit and RC; do not move an existing immutable image or Git tag.

A production rollback does not rewrite release history or delete the Git and image tags created by the failed/newer release.
