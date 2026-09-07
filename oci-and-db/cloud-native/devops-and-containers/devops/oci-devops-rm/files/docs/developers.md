# Developer Guide

This section is for application and component developers. The stack gives each component an independent source repository, validation pipeline, image build, Helm chart, dev deployment, and release path. Developers do not need to maintain the cluster tool catalog or cluster-wide Kubernetes resources.

```mermaid
flowchart LR
  Branch["Feature branch"] --> PR["Pull request"]
  PR --> Tests["<component>-pr"]
  Tests --> Main["Merge to main"]
  Main --> Build["<component>-build"]
  Build --> Image["Multi-arch image:<sha7>"]
  Image --> Dev["Deploy dev"]
  Dev --> RC["Create release candidate"]
  RC --> Staging["Deploy staging"]
  Staging --> Approval["Review diff and approve"]
  Approval --> Prod["Deploy production"]
  Prod --> Final["Final image and Git tag"]
```

## Repositories Developers Use

| Repository | Ownership and purpose |
| --- | --- |
| `<component>` | Application code, `Dockerfile`, and `.oci-devops/pull-request-pipeline.yaml` |
| `<application>-chart` | Component charts under `<application>/charts/<component>` |
| `pipelines` | Platform-owned starter build specifications and scripts; change only when evolving the common delivery model |

The seeded PR build specification is intentionally a placeholder. Replace it with tests appropriate to the component's language, runtime, and integration boundaries. The generic main build expects a `Dockerfile`; use a multi-stage Dockerfile to keep language-specific compilation and tooling inside the component repository.

The default main build specification is `<component>-build-pipeline.yaml`. Stack configuration can set a component `build_spec_path` in the `pipelines` repository. Several components can share a specification such as `java/java-build-pipeline.yaml`. Resource Manager creates a missing custom path and its parent folders from the default template once; the DevOps engineer owns all later changes and Resource Manager never refreshes the file.

## Daily Workflow

1. Create a feature branch in the component repository.
2. Open a pull request to `main` and make `<component>-pr` pass.
3. Merge the pull request. `<component>-build` publishes a multi-architecture image tagged with the 7-character Git SHA and deploys it to dev.
4. Test component chart changes in dev by changing only that component's chart directory.
5. When the commit is ready for promotion, run `<component>-release-build` with a tag such as `1.0.0-rc.1`.
6. Verify staging and approve production.
7. Confirm the final image and source commit are tagged `1.0.0` after production succeeds.

## Platform Prerequisites

Before a component can deploy, a platform owner runs `<application>-bootstrap`. Its independent noprod and prod stages initialize the configured namespaces and OCIR pull secrets in parallel. The application baseline remains owned exclusively by `<application>-deploy`. Component developers normally consume those resources rather than manage them.

## Continue Reading

- [Developer Runbooks](developer-runbooks.md) gives step-by-step procedures for routine component work and rollback.
- [Developer Workflow](developer-workflow.md) describes every pipeline stage and versioning rule.
- [Chart Lifecycle](chart-lifecycle.md) explains application baseline and component chart ownership.
- [Responsibilities](responsibilities.md) clarifies the boundary between developers, cluster administrators, and stack owners.
- [Troubleshooting And Recovery](troubleshooting-recovery.md) covers common build, deployment, and release failures.
- [Security Guidance](security.md) describes credentials, image supply-chain, and namespace expectations.
- [Naming Conventions](naming-conventions.md) lists derived repository, image, chart, release, and pipeline names.
- [Architecture](architecture.md) shows how the developer path relates to OCI DevOps and OKE.
