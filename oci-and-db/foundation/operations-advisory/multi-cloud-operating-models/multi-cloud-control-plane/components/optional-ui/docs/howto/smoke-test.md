# Pre-production smoke test

Use this check before enabling the optional UI for end users. Work only with a
disposable, already handed-off project repository that is explicitly approved
for test pull requests.

## Prerequisites

- The UI is running with a production-quality `SESSION_SECRET`.
- The GitHub OAuth callback is exactly `<APP_URL>/callback`.
- Your user can read `gitops-templates` and has write access to the disposable
  project repository.
- The project name matches `PROJECT_REPO_PREFIX`.
- Branch protection and the normal plan/check approval gate are enabled.

## Acceptance check

1. Open `/health` and confirm HTTP 200 with `status: healthy`.
2. Sign in through GitHub OAuth. Confirm the project selector shows only
   repositories your user can access.
3. Select the disposable project and open the resource catalog. Prepare one
   small non-production request and inspect the generated pull request.
4. Confirm the change uses the expected regional manifest and contains no
   literal password, credential, unresolved customer value, IAM foundation
   resource, or unapproved path.
5. Confirm the Terraform plan belongs to the current commit and that merge
   requires independent approval.
6. If OCI inventory contains an approved target, prepare one supported Day 2
   request and confirm its display name exactly matches Terraform state.
7. Confirm the dashboard and audit view show the new pull request and its
   workflow status.

The UI passes when it can prepare the expected pull request but cannot merge,
approve, call a cloud API, write a shared/template repository, or bypass a
failed repository-state check.

Close the test pull requests and delete their branches unless they are part of
an approved non-production deployment. Retain the evidence required by your
change-management process.

If any check fails, disable UI access and use the standard GitHub pull-request
flow while the OAuth, permissions, repository state, or application issue is
corrected.
