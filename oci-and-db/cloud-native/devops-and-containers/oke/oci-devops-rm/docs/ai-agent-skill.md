# AI Agent Skill

The repository includes a portable skill that helps users operate the OKE
DevOps Starter. It covers application PR validation, immutable builds, release
promotion, application bootstrap, cluster-tool administration, deployment
verification, rollback, and troubleshooting.

The skill follows the Agent Skills `SKILL.md` convention. Any AI agent that can
load that format can use it. For agents without automatic skill discovery, add
the extracted directory or its `SKILL.md` to the task context.

## Download

Download [use-oke-devops-starter.zip](../downloads/use-oke-devops-starter.zip).
The archive contains one self-contained `use-oke-devops-starter` directory.

## Install

Extract the directory into the skills location supported by your AI agent. For
OpenAI Codex, use:

```text
~/.codex/skills/use-oke-devops-starter/SKILL.md
```

Start the agent with access to the generated OCI DevOps project, its
repositories, and the relevant OCI or Kubernetes tools. With Codex, invoke
`$use-oke-devops-starter`; other agents can select the skill through their own
skill-discovery mechanism.

The skill operates the deployed solution. It does not maintain this Terraform
stack or grant permission to approve production, release, decommission, or
delete resources.

## Rebuild The Download

After changing files under `.agents/skills/use-oke-devops-starter`, run:

```bash
bash script/package_user_skill.sh
```

The generated download is intentionally excluded from the Resource Manager
deployment archive, together with the workspace `.agents` directory and
`AGENT.md`.
