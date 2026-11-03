# Solution Skill Release Assets

Every new DevOps and GitOps release includes its portable agent skills as
separate release assets:

| Release tag | Required assets |
| --- | --- |
| `oci-devops-rm-*` | `oke-devops-starter.zip` |
| `oke-gitops-*` | `manage-oke-with-argocd.zip`, `manage-oke-with-flux.zip` |

`release-agent-skills.yml` builds and uploads these archives when a release is
published. It checks out the release tag, not the default branch, so skill
contents match the released solution. Other solution releases are unaffected.
Re-running the workflow replaces only these skill assets.

For release preparation, run from the repository root:

```bash
python3 .github/scripts/package-agent-skills.py --asset devops --output-dir /tmp/devops-release
python3 .github/scripts/package-agent-skills.py --asset gitops --output-dir /tmp/gitops-release
```

The packager includes only tracked files under the relevant skill directories,
with a single installable directory per ZIP. Script permissions are preserved.
Skill archives are distributed alongside the Resource Manager deployment ZIP;
they are not nested inside it. GitOps continues to seed its engine-specific
skill into the generated repository.
