# AI Maintainer Skill

The repository includes a Codex skill for maintainers who change, validate, package, or functionally test the OKE DevOps Starter. It teaches an AI agent the stack architecture, ownership boundaries, OCI constraints, validation workflow, and release-package rules.

## Download And Install

Download [oci-devops-starter-maintainer.zip](../downloads/oci-devops-starter-maintainer.zip), then extract the contained `oci-devops-starter-maintainer` directory into:

```text
~/.codex/skills/
```

The installed entry point should be:

```text
~/.codex/skills/oci-devops-starter-maintainer/SKILL.md
```

Start Codex from the repository root and ask it to use `$oci-devops-starter-maintainer`. The skill is for maintaining this solution, not for operating the generated application or cluster-admin pipelines.

## Rebuild The Download

After changing files under `.agents/skills/oci-devops-starter-maintainer`, run:

```bash
bash script/package_maintainer_skill.sh
```

The generated download is intentionally excluded from the Resource Manager deployment archive, together with the workspace `.agents` directory and `AGENT.md`.
