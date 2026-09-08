# GitHub interface

Use the GitHub interface when you want to edit the approved JSON file directly.
First read the common [request lifecycle](request-lifecycle.md).

## GitHub website

1. Open the required manifest in your project repository and select **Edit**.
2. Apply the catalog entry described in the request lifecycle.
3. Select **Create a new branch for this commit and start a pull request**.
4. Name the branch and commit with the change reference and requested resource
   or operation.
5. Open the pull request, record the change reference, review the plan or
   check, obtain approval, and merge.
6. Verify the post-merge workflow and cloud outcome.

## GitHub CLI

Set the repository, branch, and manifest for one request:

```bash
export PROJECT_REPOSITORY=example-enterprise/nonprod-orders
export BRANCH=request/orders-api-dev
export MANIFEST=oci/dev/eu-frankfurt-1/compute/compute.json

gh repo clone "$PROJECT_REPOSITORY"
cd "${PROJECT_REPOSITORY##*/}"
git switch -c "$BRANCH"
```

Edit the file, then validate and publish it:

```bash
jq -e . "$MANIFEST" >/dev/null
git add "$MANIFEST"
git commit -m "CRQ1234: Request orders API development VM"
git push -u origin "$BRANCH"
gh pr create --fill
```

Do not merge until the plan or check and required approval are complete. The
[request lifecycle](request-lifecycle.md#complete-or-remove-a-request) explains
how to clear a completed operation or remove a resource.
