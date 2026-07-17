# Optional Codex app assistant

The Project GitOps plugin helps Project Teams prepare supported infrastructure
and lifecycle requests in the Codex app. It reads the approved catalog and
project repository, validates the change, and requires confirmation before
pushing a branch or opening a pull request.

Copy `plugins/project-gitops`, replace `__CUSTOMER_ORG__`, and install it through
your approved Codex plugin process. The user needs the Codex app with local shell
access, authenticated GitHub CLI access, repository permission, and the
deployment contract generated during setup.

The assistant cannot merge or approve pull requests, control workflows, call
cloud APIs, accept raw passwords, or perform unavailable Azure or Google Day 2
operations. Read-only work creates no persistent local files. Normal GitHub pull
requests remain fully supported without the assistant.
