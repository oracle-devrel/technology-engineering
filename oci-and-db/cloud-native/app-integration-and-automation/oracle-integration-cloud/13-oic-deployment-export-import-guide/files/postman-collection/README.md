# OIC Project Export Import Postman Collection

This collection helps you retrieve OIC project deployments and export or import OIC project archives. It uses OAuth 2.0 Client Credentials authentication; Basic Authentication is not supported for Oracle Integration Developer APIs.

## Setup

Import `OIC Project Export Import.postman_collection.json` into Postman. Create or select an environment and provide these variables:

| Variable | Description |
|---|---|
| `access_token_url` | OAuth token endpoint |
| `client_id` | OAuth client ID |
| `client_secret` | OAuth client secret |
| `scope` | OAuth scope required by the client |
| `integration_instance` | Oracle Integration service instance name |
| `project_id` | OIC project identifier, for example `HQ_ERP_PROJECT` |

Use uppercase project names and codes in the export request bodies. Update the import request to point to the local `.CAR` archive you want to upload.

## APIs

### Get Project Deployments

`GET /ic/api/integration/v1/projects/{{project_id}}/deployments`

Lists deployments for the selected project. Use the returned deployment identifier as the `label` when exporting one deployment.

### Export Project

`POST /ic/api/integration/v1/projects/{{project_id}}/archive`

Exports the complete project as a `.CAR` archive. Keep `label` empty in the request body.

### Export Deployment

`POST /ic/api/integration/v1/projects/{{project_id}}/archive`

Exports one deployment as a `.CAR` archive. Set `label` to the deployment identifier, for example `DEPLOYMENT1`.

### Import Project or Deployment

`POST /ic/api/integration/v1/projects/archive`

Imports a previously exported `.CAR` archive. The request uses `multipart/form-data` with the binary field named `file`. The destination project or deployment must not already exist; otherwise, the import fails with a conflict error.

## References

- [Authentication](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/Authentication.html)
- [Export a Project](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/op-ic-api-integration-v1-projects-id-archive-post.html)
- [Import Add a Project](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/op-ic-api-integration-v1-projects-archive-post.html)

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
