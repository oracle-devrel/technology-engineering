# Guide for AI-assisted Flux administration

An AI agent must treat Git as desired state and each cluster's local Flux
objects as observation surfaces. Install the portable package described in
[the skill installation guide](install-agent-skill.md).

Before changing anything, identify the exact cluster, repository, namespace,
application, component, environment, and profile. Read this repository's main
README, the relevant application directory, and—when applicable—the
`apps-config` or `fleet-config` documentation.

The deterministic workflow is:

1. inspect repository state and existing ResourceSets, inputs, sources, paths,
   dependencies, and generated object names;
2. make the smallest Git change in the repository that owns the concern;
3. render every changed Kustomize root and affected ordered Helm selection;
4. review pruning, identity overlap, namespace changes, secrets, exposure,
   storage, and resources;
5. commit through review only when authorized;
6. observe Ready conditions on the target cluster; fix or revert Git.

Never use a central-cluster assumption: Flux fleet members are decentralized.
The primary uses `cluster-config`; reusable fleet placement belongs in
`fleet-config`; developer payload belongs in `apps-config`. Additional members
have no `cluster-config` source and are installed through their own private OCI
DevOps environment and pipeline.

Every report must state targets, impacted files, validation, exact changed or
pruned Kubernetes identities, external actions, and rollback.
