# MCCP technical architecture

For the operating model and a worked example of why it matters, start with [How the Control Plane works](architecture.md).

## Repository model

| Shared repository | Purpose |
| --- | --- |
| `platform-ci` | Reusable workflows for validation, planning and execution |
| `gitops-templates` | Approved resource and operation templates |
| `nonprod-project-template` | Starting point for a project's non-production repository |
| `prod-project-template` | Starting point for a separate production repository |

A project uses `nonprod-<project>` for `dev`, `test` and `uat`. When production is enabled it uses `prod-<project>` for `prod`, with its own handoff and runner boundary. Terraform state is separated by organization, project repository, cloud, environment and region.

Project repositories store configuration and foundation references. OCI and Google Cloud consume their reviewed environment handoffs. Azure uses the existing foundation inputs in the request or resource JSON, with optional handoff notes, and the runner's `ARM_*` configuration provides subscription and authentication. Reviewers check that those references point to the intended foundation. The workflows validate change paths, scope and supported manifest shapes. The runner's cloud permissions govern access to the referenced resources.

## Execution and trust boundary

GitHub, the optional UI and the optional Codex plugin prepare pull requests. The project workflow reads the proposed change and calls Platform CI for a Terraform plan or Ansible check. The review uses evidence for the current revision. After merge, the matching workflow uses the merged configuration, the intended state scope and the trusted runner identity. GitHub records the workflow outcome. A successful plan or check describes proposed work. The post-merge run records execution.

Cloud Operations manages the runner identities and keeps production and non-production separate. The reference can run OCI, Azure and Google Cloud jobs on trusted OCI hosts configured with the required labels and cloud identities. The Project Team needs project repository access and can manage its workload secrets within the approved Vault scope. See the [security controls](security.md) and the [request lifecycle](../usage/request-lifecycle.md).

## Target operating model

Cloud Operations owns the foundation, state, runner identities and project handoff. Project Teams can request the catalog items available within their project's approved scope. New cloud integrations and catalog entries follow the same request, review and execution process. See the [capabilities supplied with this reference](support.md).

## Extension model

Customers can start with the supplied catalog and extend it as their needs grow. Cloud Operations owns the platform changes that make each extension available to Project Teams:

| Extension | Delivery path to add or update |
| --- | --- |
| Resource | Catalog profile and destination manifest, validation, Terraform module or adapter, workflow routing and plan/apply evidence. |
| Operation | Catalog manifest and allowed fields, state-backed target inventory, approved playbook or action, check and execution evidence. |
| Cloud integration | Foundation inputs and handoff contract, cloud identity, runner routing, state scope, adapter and catalog entries for the first supported requests. |

Cloud Operations implements and reviews the complete delivery path before making a resource or operation available:

1. Prepare the required foundation references, permissions and handoff.
2. Publish the catalog template and its semantic validation.
3. Implement the orchestrator or execution action and route it explicitly in the workflows. An operation needs allowed manifest fields, inventory extraction and a provider-specific playbook or action.
4. Set up isolated state, a scoped runner identity and any required secret access.
5. Document and validate the full reviewed request and execution path.

For example, the existing OCI Compute [`deploy-agent` operation](../../repository-sources/gitops-templates/operations-catalog/specs/oci/deploy-agent.md) writes `/opt/agents/<agent_type>.installed` over SSH to demonstrate execution on an exact target from Terraform state. To use a customer's installer, Cloud Operations replaces the marked extension point in Platform CI's `ansible/playbooks/common/oci/deploy-agent/apply.yml` with a platform-owned role or task import through a reviewed platform change. In the same change, update `verify.yml` in that directory to verify the installed agent; the supplied task only checks the marker. Keep the wrapper and its precheck, apply and verify phases. Map validated agent types to approved implementations; the request must not choose commands, URLs, playbooks or paths.

Once published, an extension follows the same request, approval, execution and recorded-result process as the supplied catalog. Preserve private-by-default workloads, explicitly reviewed public profiles, one cloud, environment and region per pull request, independent human approval, least privilege and separate duties. The [repository source index](../../repository-sources/README.md) identifies the components that implement these controls.
