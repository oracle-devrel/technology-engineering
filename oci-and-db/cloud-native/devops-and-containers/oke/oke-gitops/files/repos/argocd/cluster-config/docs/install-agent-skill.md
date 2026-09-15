# Install the OKE Argo CD agent skill

The generated `cluster-config` repository includes a self-contained skill at:

```text
skills/manage-oke-with-argocd/
```

It gives an AI agent the repository contracts, safety rules, use-case routing,
templates, local validation, change-impact analysis, fleet conventions, and
troubleshooting workflow required to manage this OKE GitOps solution.

## Prerequisites

The workstation needs:

- Git;
- `kubectl` with Kustomize support;
- Helm when managing Helm applications;
- network and Kubernetes credentials only when observing or bootstrapping a
  live cluster;
- OCI CLI only for OCI operations such as kubeconfig creation or Vault work.

Local repository planning and rendering do not require live cluster access.

## Install for Codex-compatible agents

Copy the complete skill directory into the agent's skills directory. For
Codex, use `$CODEX_HOME/skills` when configured or `~/.codex/skills` otherwise:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/manage-oke-with-argocd \
  "${CODEX_HOME:-$HOME/.codex}/skills/manage-oke-with-argocd"
```

Restart or reload the agent so it discovers the skill. Invoke it explicitly
with `$manage-oke-with-argocd`, or ask for an OKE/Argo CD GitOps operation that
matches its description.

## Install for another local agent

If the agent supports the Agent Skills folder convention, install the same
directory according to that product's instructions. If it does not, configure
the agent to:

1. load `SKILL.md` as its operating instructions;
2. preserve access to the bundled `references/`, `scripts/`, and `assets/`
   directories;
3. execute the scripts from the skill directory rather than copying their text
   into prompts;
4. load only the reference selected by `SKILL.md` for the current task.

The content deliberately does not depend on Codex tools, MCP servers, cloud
connectors, or conversation memory. Product-specific metadata is isolated in
`agents/openai.yaml`; other agents may ignore it.

## Verify the installation

From a clone of `cluster-config`, `apps-config`, or `fleet-config`, ask the
agent to use the skill and run:

```bash
<installed-skill>/scripts/preflight.sh .
<installed-skill>/scripts/validate.sh .
<installed-skill>/scripts/impact.sh . HEAD
```

`preflight.sh` must identify the standalone generated repository. The
validation script renders every Kustomize root and Helm combination it finds.
The impact script reports changed control files and highlights tracked
deletions for pruning review. `diff-kustomize.sh` and
`diff-helm-selection.sh` compare the selected deployment unit before and after
the worktree change so the agent reports only Kubernetes objects that actually
change.

## What the skill must not contain

The skill contains no kubeconfig, token, password, Secret data, tenancy OCID,
cluster endpoint, or customer-specific desired state. Runtime access remains a
customer-controlled workstation and identity concern.

## Updating the installed copy

The skill in Git is authoritative. Review its Git diff, then replace the
installed directory with the new complete directory. Do not merge old and new
script sets selectively; that can leave references and validation behavior out
of sync.
