# OIC Project and Deployment Export and Import Guide

Use the Oracle Integration 3 Developer API to export an entire project or one deployment, then import its archive into another environment. Export returns a downloadable `.CAR` archive. Import adds a project or deployment that is not already present in the target environment.

## Prerequisite OAuth Authentication

OAuth is required for Oracle Integration Developer APIs. Basic Authentication is not accepted by these APIs. Configure an OAuth client, obtain a valid access token, and send it with every request:

```http
Authorization: Bearer <ACCESS_TOKEN>
```

1. Configure an OAuth client and choose the appropriate grant type.
2. Request an access token.
3. Call the Developer API using the design-time URL and Bearer token.
4. Refresh the token when it expires.

Further details:

- [Oracle documentation - Security Authentication and Authorization](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/Authentication.html)
- [Step by step OAuth setup tutorial video](https://youtu.be/UrptzZbycm4?si=xz27moIXhua531m_)

## Prepare the request

Replace the following values for your environment:

| Placeholder | Meaning |
|---|---|
| `<DESIGN_HOST>` | Oracle Integration design host |
| `<ACCESS_TOKEN>` | Valid OAuth access token |
| `<INTEGRATION_INSTANCE>` | Oracle Integration service instance name |
| `<PROJECT_ID>` | Project identifier, for example `TEST_PROJECT` |
| `<ARCHIVE_FILE>` | Local `.CAR` archive, for example `TEST_PROJECT.CAR` |

Use uppercase project values consistently. The examples use `TEST PROJECT`, `TEST_PROJECT`, and `DEVELOPED`. The `LABEL` value identifies a deployment.

## Export an entire project

**Endpoint**

```text
POST https://<DESIGN_HOST>/ic/api/integration/v1/projects/<PROJECT_ID>/archive?integrationInstance=<INTEGRATION_INSTANCE>
```

**Project export payload**

```json
{"name":"TEST PROJECT","code":"TEST_PROJECT","type":"DEVELOPED","builtBy":"","label":""}
```

Keep `label` empty for a full project export.

```bash
curl -X POST \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"TEST PROJECT","code":"TEST_PROJECT","type":"DEVELOPED","builtBy":"","label":""}' \
  -o "TEST_PROJECT.CAR" \
  "https://<DESIGN_HOST>/ic/api/integration/v1/projects/TEST_PROJECT/archive?integrationInstance=<INTEGRATION_INSTANCE>"
```

The successful response is an `application/octet-stream` archive.

## Export a single deployment

Use the same endpoint and supply the deployment identifier in `label`.

```json
{"name":"TEST PROJECT","code":"TEST_PROJECT","type":"DEVELOPED","builtBy":"","label":"01.00.0000"}
```

```bash
curl -X POST \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"name":"TEST PROJECT","code":"TEST_PROJECT","type":"DEVELOPED","builtBy":"","label":"01.00.0000"}' \
  -o "TEST_PROJECT_01.00.0000.CAR" \
  "https://<DESIGN_HOST>/ic/api/integration/v1/projects/TEST_PROJECT/archive?integrationInstance=<INTEGRATION_INSTANCE>"
```

## Import an exported archive

**Endpoint**

```text
POST https://<DESIGN_HOST>/ic/api/integration/v1/projects/archive?integrationInstance=<INTEGRATION_INSTANCE>
```

Upload the previously exported `.CAR` archive as `multipart/form-data` using the binary field named `file`.

```bash
curl -X POST \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "file=@TEST_PROJECT.CAR" \
  -F "type=application/octet-stream" \
  "https://<DESIGN_HOST>/ic/api/integration/v1/projects/archive?integrationInstance=<INTEGRATION_INSTANCE>"
```

The project or deployment being imported must not already exist in the target environment. A conflict returns HTTP `409` when the project already exists.

| Status | Meaning |
|---|---|
| `200` | Successful import |
| `400` | No file uploaded |
| `409` | Project already exists |
| `500` | Server error |

## Source documentation

- [Export a Project](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/op-ic-api-integration-v1-projects-id-archive-post.html)
- [Import Add a Project](https://docs.oracle.com/en/cloud/paas/application-integration/rest-api/op-ic-api-integration-v1-projects-archive-post.html)


# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.