# Stack Operations

This guide is for the team packaging, applying, and validating the Resource Manager stack. For day-to-day OKE tool and cluster-resource administration, start with the [Cluster Operations Guide](cluster-operations.md).

Before distributing or upgrading the stack, review [Template Ownership And Upgrades](template-ownership.md), [Responsibilities](responsibilities.md), and [Security Guidance](security.md).

## Applying The Stack

Build and upload a fresh stack zip when the Terraform templates change. Keep generated local context out of the zip, especially:

- `AGENT.md`
- `.agents`
- `.git`
- `.terraform`
- local state and plan files

After apply, Resource Manager creates the starter OCI DevOps resources. Existing application/component DevOps resources ignore user-editable changes, and repository seeders never overwrite an existing path.

Repository initialization is intentionally create-only:

- Existing source repositories are adopted without modification.
- Existing shared and application files are preserved.
- Adding an application or component adds only its missing pipeline/chart paths.
- Removing an application or component from the JSON does not delete its Git files, although Terraform can still destroy its OCI resources.
- Template improvements from a newer stack archive are not applied to existing repositories automatically.

Review and merge newer template changes through Git when a customized repository should adopt them.

## Application Information

After a successful apply, the stack's Application Information tab organizes outputs into:

- Start Here: project, configured applications/components, namespaces, and derived next steps.
- Repositories: component source and application chart repository URLs.
- Build Pipelines: PR, build, release-build, and application package pipeline OCIDs.
- Deployment Pipelines And Environments: namespace initialization, application/component deployment pipelines, and both OKE environments.
- OCIR: application charts, component charts, and component image repositories.
- Cluster Administration: admin repository, shared admin build pipelines, Generic Artifact repository, and cluster/tool deployment pipelines.

Map-valued outputs are rendered as structured JSON instead of single-line copyable strings. The primary action opens the shared pipelines repository.

## Suggested Local Checks

Before uploading the stack:

```bash
terraform fmt -check -recursive
terraform validate
bash -n repos/pipelines/script/*.sh script/*.sh
helm lint repos/generated/charts/<application>/<application>
helm lint repos/generated/charts/<application>/<application>/charts/<component>
```

The generated chart paths depend on the configured applications.

## Functional Test Checklist

For each application:

1. Run `<application>-bootstrap` and confirm both namespace stages succeed, or invoke only the target stage being tested.
2. Confirm the configured baseline chart version is published in OCIR.
3. Run `<application>-deploy` when testing full baseline promotion.
4. Confirm releases `<application>-noprod` and, after approval, `<application>` exist.

For each component:

1. Open a pull request and verify `<component>-pr` succeeds.
2. Merge to `main`.
3. Verify `<component>-build` produces only the 7-character SHA image tag.
4. Verify `<component>-dev-deploy` updates release `<component>-dev`.
5. Run `<component>-release-build` with `release_tag=1.0.0-rc.1`.
6. Verify staging release `<component>-staging`.
7. Review staging, then approve production.
8. Verify prod release `<component>`, final image tag `1.0.0`, and final Git tag `1.0.0`.

For chart lifecycle:

1. Modify a component chart and verify only that component chart packages and dev redeploys.
2. Modify an umbrella chart file outside `charts/**` and verify only `<application>-package` and `<application>-deploy` run.

For cluster administration:

1. Open a PR changing one cluster baseline or one tool path and verify `cluster-admin-pr` succeeds.
2. Merge the PR and verify `cluster-admin-build` selects only changed stages.
3. Verify `cluster-admin-mirror-charts` skips chart versions already present in OCIR.
4. Verify the values artifact version equals the full Git commit SHA.
5. Verify `cluster-admin-noprod` runs its orchestrator immediately and deploys only selected changes.
6. Verify `cluster-admin-prod` pauses for approval and then runs the same orchestration behavior.
7. Change independent tools together and verify their stages run in parallel; declare `depends_on` and verify the dependent tool waits.
8. Confirm supplemental resources are created only in the configured tool namespace.

## Cleanup

To remove application workloads from a test cluster, delete the application namespaces:

```bash
kubectl delete namespace <application>
```

For the default sample:

```bash
kubectl delete namespace sample-app
```

## Capacity Notes

Dev, staging, and prod releases can all run in the same test cluster if prod points to pre-prod. That is convenient for demos, but it consumes more CPU and memory. If pods remain pending with an `Insufficient cpu` event, scale down old dev or staging deployments, add capacity, or use a separate production cluster.
