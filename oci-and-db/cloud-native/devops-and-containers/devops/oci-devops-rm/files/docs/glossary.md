# Glossary

| Term | Meaning |
| --- | --- |
| Application | A logical product containing one or more components and one shared Kubernetes namespace baseline |
| Component | An independently built, charted, deployed, and released workload inside an application |
| Application baseline | The umbrella Helm chart containing shared namespace resources but no component workloads |
| Application bootstrap | Idempotent pipeline with parallel stages that initialize one application's noprod and prod namespaces and pull secrets |
| Component chart | A standalone Helm chart deployed independently for dev, staging, and prod |
| SHA image | The immutable main-build image tagged with exactly seven Git commit characters |
| Release candidate | A promoted SHA image and Git tag such as `1.0.0-rc.1` |
| Final release | The production image and Git tag derived by removing `-rc.N` |
| Noprod | The physical OKE target shared by non-production application environments and operations configuration |
| Stage catalog | A cluster-admin deployment pipeline whose tool and baseline stages are invoked selectively |
| Dependency wave | A set of independent selected tools that can deploy in parallel before dependent tools |
| Production Helm verification | Production-only deployment stage that checks the final release with `helm status` before Git tagging |
| Decommission pipeline | Manual cluster operation that deletes one tool's supplemental resources and uninstalls its Helm release; production requires approval |
| Supplemental resources | Tool-specific namespaced YAML applied after the tool's Helm chart |
| Cluster baseline | Cluster-scoped YAML applied after selected tool stages |
| Values artifact | An OCI artifact containing Helm values; cluster-admin versions it with the full configuration commit SHA |
| Configuration commit | The exact `cluster-admin` Git commit used to select and deploy cluster changes |
| Template ownership | The model in which Terraform creates starter resources while preserving later user customization |
| Development mode | Internal stack-packaging mode that allows the development stack to refresh template resources |
