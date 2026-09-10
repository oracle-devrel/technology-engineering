# Workflow

1. Identify the handed-off repository and requested environment. A non-prod
   request must name `dev`, `test`, or `uat`; a production request uses only
   `prod`. Run `gh repo view <owner/repository> --json
   nameWithOwner,isPrivate,defaultBranchRef,sshUrl` and stop unless it is the
   expected private project repository with default branch `main`.
2. Read only the selected catalog entry from `<owner>/gitops-templates` at
   `main`, for example `gh api -H "Accept: application/vnd.github.raw+json"
   "repos/<owner>/gitops-templates/contents/<catalog-path>?ref=main"`.
   Use `resources-catalog` for infrastructure: render its structure exactly,
   replacing only documented placeholders, then merge the selected fragment
   into the existing regional manifest without replacing other root keys.
   Preserve all literal fields, types, and collections. Populate a collection
   only when its catalog fragment supplies an entry shape; an empty collection
   with no entry template authorizes zero entries. Stop rather than infer a
   field, CIDR, source, protocol, port, or rule that the catalog does not
   model. `project_nsgs_template.json` contains the complete NSG object plus
   optional child patterns for one TCP ingress rule and one TCP egress rule.
   Render zero or more of those child patterns only when requested. For an
   existing NSG, merge only the requested child pattern into that NSG; do not
   repeat or replace its creation fields. `protocol` is the literal catalog
   value `TCP`; never replace it with a provider number such as `6`. For
   ingress render only their published `src`, `src_type`, `dst_port_min`, and
   `dst_port_max` fields; for egress use `dst` and `dst_type` instead. Do not
   add nested provider `tcp_options`. A `0.0.0.0/0` ingress source is allowed
   only when explicitly requested and must be identified as public exposure in
   the preview. Use
   `operations-catalog` for OCI lifecycle work: create, modify, or
   clear one file under `oci/<environment>/<region>/lifecycle_operations/`. For every
   OCI ADB or Compute request, select the named approved capacity profile from
   the catalog and preserve all of its literal capacity, license, image, and
   auto-scaling values. Do not combine profiles or change their values. For every
   OCI ADB, replace the catalog's generic administrator-password placeholder
   with its own token formed from the environment and normalized database
   mapping key, as defined in [setup](setup.md). Do not reuse a token for two
   databases. A clear only removes an existing operation request; it does not
   call OCI.
3. Derive one stable branch name from the CRQ and requested destination:
   `agent/<crq-lower>-<cloud>-<environment>-<region>-<resource-key>`. The
   `resource-key` is the catalog mapping key or operation filename, normalized
   to lowercase letters, digits, and hyphens. Before creating it, check both
   the remote branch (`git ls-remote --exit-code --heads origin
   refs/heads/<branch>`) and open pull requests (`gh pr list --repo
   <owner/repository> --head <branch> --state open --limit 1 --json
   number,url`) for that exact name. If either exists, stop and report it;
   never add a suffix or create a duplicate PR.
4. Create a disposable clone from the current `main`: `git clone --branch main
   <repository-url> <temporary-directory>`, `git fetch origin main`, then
   `git switch -c <branch> origin/main`. Edit only the one catalog-selected
   manifest or operation file. Do not infer fields, query cloud APIs, or
   implement resource-specific checks locally.
5. Before any GitHub write, confirm that the candidate still starts from the
   current `main`. Inspect its runtime-secret tokens. A preview is invalid
   unless it lists the required secret bundle and every required JSON member
   for each runtime token in the candidate. For example, two `dev` ADBs keyed
   `project45-adb1` and `project45-adb2` require
   `GITOPS_SECRET_VALUES_DEV` with these distinct members. Only when the bundle
   does not yet exist, the administrator may create it with this complete JSON
   object:

   ```json
   {
     "DEV_PROJECT45_ADB1_ADMIN_PASSWORD":"<set-the-first-ADB-admin-password>",
     "DEV_PROJECT45_ADB2_ADMIN_PASSWORD":"<set-the-second-ADB-admin-password>"
   }
   ```

   State that the administrator replaces only the angle-bracket placeholders
   before saving it. If the bundle already exists, show only the missing member
   keys as a JSON fragment and instruct the administrator to merge them through
   the approved secret process without replacing existing members; the agent
   cannot read or reconstruct their values. For OCI ADB, include the published
   password policy: 12 to 30 characters, at least one uppercase letter,
   lowercase letter, and digit, with no double quote and no `admin` substring
   in any casing. Do not read or test that secret; state it as a prerequisite.
   Show a semantic preview naming the repository, branch, selected path,
   requested outcome, destructive or replacement impact, CRQ, those
   prerequisites, and `GitHub writes: none`. Only then ask for the standalone
   `confirm` reply.
6. After confirmation, re-fetch `origin/main`; if it or the candidate differs
   from the preview, stop, rebuild the candidate, and request a new preview.
   Stage only the selected path, commit, push the branch, and create one PR
   with a title and body that include the CRQ: `gh pr create --base main --head
   <branch> --title <title> --body <body>`. Do not merge, approve, dispatch,
   rerun, or cancel a workflow.
7. The protected template triggers Platform CI; never launch a workflow
   manually. Derive one expected workflow name from the selected repository
   and path:

   | Change | Expected workflow |
   | --- | --- |
   | Non-prod infrastructure manifest | `Shared non-production Terraform` |
   | Production infrastructure manifest | `Production Terraform` |
   | Non-prod OCI lifecycle manifest | `Shared non-production OCI operations` |
   | Production OCI lifecycle manifest | `Production OCI operations` |

   Its PR trigger is `pull_request_target`, so do not filter runs as
   `pull_request`. Read only that workflow with `gh run list --repo
   <owner/repository> --workflow <expected-workflow> --branch <branch> --limit
   10 --json databaseId,status,conclusion,workflowName,url,event,headSha`.
   Require exactly one `pull_request_target` run whose `headSha` is the PR head
   commit; if absent or ambiguous, stop rather than selecting another run. Poll
   it with `gh run view <databaseId> --repo <owner/repository> --json
   status,conclusion,url` every 15–30 seconds until terminal. Report the PR
   and workflow URL; Platform CI owns validation, plan, and apply.
