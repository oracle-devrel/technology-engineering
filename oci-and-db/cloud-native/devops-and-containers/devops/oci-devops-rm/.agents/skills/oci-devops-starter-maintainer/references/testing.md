# Validation And Functional Testing

## Local Validation

Run the Skill validator from the repository root:

```bash
bash .agents/skills/oci-devops-starter-maintainer/scripts/validate.sh
```

It checks Terraform formatting and validation, Python regressions, shell syntax, and every generated Helm chart found in the workspace.

When `schema.yaml` changes, also validate it against the current OCI Resource Manager metadata JSON Schema supplied for the project. Confirm Resource Manager dependencies, visibility, required fields, regex validation, multiline JSON controls, and defaults in the graphical form after upload.

## Archive Verification

After `./update.sh`, list the archive and reject it if it contains any of:

```text
.agents/
AGENT.md
.git/
.terraform/
terraform.tfstate
*.tfvars
*.log
credentials or private test scripts
```

Test both packaging modes after changing lifecycle or packaging logic:

```bash
./update.sh
STACK_DEVELOPMENT_MODE=true STACK_ZIP_PATH=/tmp/oke-devops-development.zip ./update.sh
```

Release mode must retain intended lifecycle ignores. Development mode must remove only the exact release ownership blocks and set the hidden development input.

## Functional Test Selection

Use the smallest test that proves the changed contract:

| Change | Minimum live test |
| --- | --- |
| Resource Manager input or output | Upload/apply and inspect the graphical form plus outputs |
| Repository seeding | Apply twice; customize between applies and prove preservation |
| Component PR pipeline | Branch, PR, PR update, successful test run |
| Component build | Main commit, SHA7 image, dev deployment |
| Component release | RC promotion, staging, approval, prod, final image and Git tags |
| Application chart | Package baseline, noprod deploy, approval, prod deploy |
| Cluster tool | PR/build selection, mirror, target cluster deployment, health check |
| Cluster DAG | Independent parallel wave plus dependent tool wave |
| Decommission | Remove only the selected release/resources and preserve unrelated objects |

## Live-Test Discipline

1. Record resource IDs and commit hashes needed to correlate runs, but do not commit them to the Skill or distributable docs.
2. Inspect build/deployment logs and resulting OCIR, Git, Helm, and Kubernetes state.
3. When pre-prod and prod share a cluster, account for release-name and namespace collisions before testing.
4. Use direct `kubectl` only for verification and requested cleanup, not as a substitute for proving OCI DevOps execution.
5. Clean cluster-admin test charts and supplemental resources after successful functional tests unless the user asks to retain them.
6. Never approve, destroy, decommission, or clean production-scoped resources without explicit authorization.
7. Emit the configured completion notification only after the requested functional-test terminal condition is reached, and stop it immediately when requested.
