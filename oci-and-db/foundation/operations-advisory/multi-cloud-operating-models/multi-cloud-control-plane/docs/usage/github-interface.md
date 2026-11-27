# GitHub interface

Use GitHub to edit a request file directly. Choose the template and find its destination in the [request lifecycle](request-lifecycle.md#manifest-paths).

Keep each pull request within one cloud, environment and region. Resource changes can share a pull request within that scope; an OCI operation uses a separate pull request with one operation file, which can include several supported targets. Creating a database and stopping another therefore requires two pull requests.

## GitHub website

1. Open the required manifest in your project repository and select **Edit**.
2. Apply the catalog entry described in the request lifecycle.
3. Select **Create a new branch for this commit and start a pull request**.
4. Name the branch and commit with the change reference and requested resource or operation.
5. Open the pull request and record the change reference. Follow the [review and execution steps](request-lifecycle.md#review-and-execute).

For the first operation, the destination file may not exist. From the repository's **Code** tab, select **Add file → Create new file** and enter the full path, for example `oci/dev/eu-frankfurt-1/lifecycle_operations/adb-lifecycle.json`. Copy the approved [`adb-lifecycle` template](../../repository-sources/gitops-templates/operations-catalog/oci/adb-lifecycle.json), replace its placeholders and use exact target display names from Terraform state. Select **Commit changes**, choose a new branch and open a pull request. GitHub's [file creation guide](https://docs.github.com/en/repositories/working-with-files/managing-files/creating-new-files) explains how `/` in the filename creates subdirectories.

## GitHub CLI

Set the repository, branch and manifest path for your request.

```bash
export PROJECT_REPOSITORY=example-enterprise/nonprod-orders
export BRANCH=request/orders-api-dev
export MANIFEST=oci/dev/eu-frankfurt-1/compute/compute.json

gh repo clone "$PROJECT_REPOSITORY"
cd "${PROJECT_REPOSITORY##*/}"
git switch -c "$BRANCH"
```

Edit the file, then validate the JSON and open the pull request.

```bash
jq -e . "$MANIFEST" >/dev/null
git add "$MANIFEST"
git commit -m "CRQ1234: Request orders API development VM"
git push -u origin "$BRANCH"
gh pr create --fill
```

For a separate first operation request, start from up-to-date `main` and create the parent directory if it is missing:

```bash
git switch main
git pull --ff-only
export BRANCH=request/CRQ1234-stop-ordersadb
export MANIFEST=oci/dev/eu-frankfurt-1/lifecycle_operations/adb-lifecycle.json
git switch -c "$BRANCH"
mkdir -p "$(dirname "$MANIFEST")"
```

Create `"$MANIFEST"` with the approved [`adb-lifecycle` template](../../repository-sources/gitops-templates/operations-catalog/oci/adb-lifecycle.json). If it already exists, review the pending or completed request before changing it. Set the Database compartment from the handoff and the exact database display names from Terraform state, with the intended `start` or `stop` action. Validate it with the same `jq` command above, then stage only that file, commit with the change reference, push the branch and open its own pull request using the commands above with an operation-specific commit message.

Check the current plan or operation check and get independent approval before merging. Use the [review and execution steps](request-lifecycle.md#review-and-execute) to verify the result. To clear an operation or delete a resource, follow the [removal steps](request-lifecycle.md#complete-or-remove-a-request).
