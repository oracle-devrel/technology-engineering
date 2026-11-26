# Optional Multi-Cloud Control Plane UI

Use a catalog form to prepare a pull request from your project repository.

1. Sign in with GitHub and choose the project, environment and region.
2. Select an approved resource or OCI operation. Choose a published size or connectivity option where the catalog offers one.
3. Fill in the request. Use the reviewed OCI or Google Cloud handoff, or supply the existing Azure foundation inputs. For OCI and Azure Autonomous Database, enter the existing Vault secret OCID dedicated to that database.
4. Enter a change reference, such as `CRQ1234`. Use `CRQ` followed by 1 to 20 digits.
5. Review and submit. Open the resulting pull request in GitHub for validation, independent review and merge. Verify the post-merge workflow there.

The form uses the catalog's fixed settings. For an OCI project network security group, it supports new groups and addition of approved TCP rules to existing groups. See the [reference capabilities](../reference/support.md) and the [request lifecycle](request-lifecycle.md).

The optional AI Operations chat is a single-presenter MVP, disabled by default. It can prepare requests conversationally in its configured OCI and Azure scope. Use GitHub to verify reviews and execution. [Setup and demo scope](../../repository-sources/optional-ui/README.md#local-chat-demo)
