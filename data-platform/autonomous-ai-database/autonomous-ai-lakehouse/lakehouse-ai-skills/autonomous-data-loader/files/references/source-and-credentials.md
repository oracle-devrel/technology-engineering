# Source and credentials

Use this reference when the user needs to connect Autonomous AI Lakehouse to OCI Object Storage or when a credential/URI problem is likely.

## Credential rules

- Prefer an existing `DBMS_CLOUD` credential name.
- Never ask the user to paste secrets into chat.
- If no credential exists, generate a `DBMS_CLOUD.CREATE_CREDENTIAL` template with placeholders.
- Tell the user to replace placeholders securely in their SQL client or secrets workflow.
- Treat credential creation as mutating and require approval before execution.

Credential template:

```sql
begin
  dbms_cloud.create_credential(
    credential_name => '<CREDENTIAL_NAME>',
    username        => '<OCI_USER_OCID_OR_USERNAME>',
    password        => '<AUTH_TOKEN_OR_SECRET_PLACEHOLDER>'
  );
end;
/
```

## OCI Object Storage URI pattern

Use fully qualified OCI Object Storage object URLs when possible:

```text
https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/<object-name-or-prefix>
```

When the user provides only bucket or prefix names, ask for or derive:

- region,
- namespace,
- bucket,
- object prefix or exact object name,
- credential name.

## Minimal source inputs

For object discovery:

- `credential_name`
- `location_uri` pointing to a bucket or prefix

For loading:

- `credential_name`
- `file_uri_list` using exact files, wildcard, or regex pattern
- `format` options
- target table or collection

## Credential troubleshooting

If `LIST_OBJECTS` or `COPY_DATA` fails with authorization or access errors, suggest checking:

- credential name exists and is accessible to the current schema,
- OCI auth token or principal configuration,
- bucket/object permissions,
- correct namespace, region, and bucket spelling,
- whether the object URI is URL-encoded when needed.
