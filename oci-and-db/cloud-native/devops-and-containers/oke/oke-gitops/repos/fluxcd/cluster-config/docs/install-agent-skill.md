# Install the OKE Flux agent skill

The generated `cluster-config` repository includes a self-contained skill at:

```text
skills/manage-oke-with-flux/
```

It contains the repository contracts, safety rules, use-case routing,
sanitized templates, local validation, impact analysis, decentralized-fleet
conventions, and troubleshooting workflow needed to operate this solution.

## Prerequisites

The workstation needs Git, `kubectl` with Kustomize support, and Helm when
managing charts. Network, kubeconfig, and OCI CLI access are needed only for
authorized live-cluster or OCI operations. Planning and rendering are local.

## Install for Codex-compatible agents

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/manage-oke-with-flux \
  "${CODEX_HOME:-$HOME/.codex}/skills/manage-oke-with-flux"
```

Restart or reload the agent. Invoke `$manage-oke-with-flux`, or ask for a
matching OKE/Flux GitOps operation.

## Install for another local agent

If the agent supports the Agent Skills folder convention, install the complete
directory using that product's mechanism. Otherwise configure it to load
`SKILL.md`, preserve relative access to `references/`, `scripts/`, and
`assets/`, execute the scripts rather than pasting them into prompts, and load
only the task-specific reference selected by `SKILL.md`.

The package does not depend on Codex tools, MCP, proprietary connectors, live
access, or conversation memory. Other agents may ignore `agents/openai.yaml`.

## Verify installation

From a standalone generated repository run:

```bash
<installed-skill>/scripts/preflight.sh .
<installed-skill>/scripts/validate.sh .
<installed-skill>/scripts/impact.sh . HEAD
```

The scripts identify the repository, render Kustomize and Helm content, and
highlight control-file/deletion changes. Use the two diff helpers for exact
before/after workload impact.

The skill contains no kubeconfig, token, password, populated Secret, tenancy
OCID, cluster endpoint, or customer-specific desired state. The Git copy is
authoritative; replace the installed directory as one reviewed unit when it is
updated.
