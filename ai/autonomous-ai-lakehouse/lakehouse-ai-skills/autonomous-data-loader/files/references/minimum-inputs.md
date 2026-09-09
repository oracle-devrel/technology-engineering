# Minimum inputs by workflow

Use this reference to avoid unnecessary clarification while still preventing unsafe assumptions.

## LIST_OBJECTS / object discovery

Minimum inputs:

- `credential_name`
- OCI Object Storage bucket or prefix URI

If the user provides only a bucket name, ask for or infer only from already-known context:

- region,
- namespace,
- bucket,
- optional prefix.

## COPY_DATA into an existing table

Minimum inputs:

- `credential_name`
- exact file URI, URI list, wildcard, or regex pattern
- target table name
- file format

Before generating the final `COPY_DATA`, run or generate:

- object discovery if the source is a prefix,
- target table existence check,
- target column inspection,
- format options.

## CSV conservative staging

Minimum inputs:

- `credential_name`
- one representative CSV file URI or homogeneous CSV prefix
- CSV header, or permission to sample the header through MCP with `DBMS_CLOUD.GET_OBJECT`
- user-approved staging table name
- delimiter if not comma or if unknown

Do not create final business DDL from a CSV header alone.

## COPY_COLLECTION JSON document load

Minimum inputs:

- `credential_name`
- JSON file URI, URI list, wildcard, or regex pattern
- collection name
- `json` versus `ejson` decision, if relevant
- whether array unpacking is needed, if the JSON root is an array

Clarify whether the user wants document-style loading or relational-table loading when intent is ambiguous.

## Troubleshooting

Minimum inputs:

- operation id, target table/collection, or enough time/context to locate the recent operation

Then use:

- `USER_LOAD_OPERATIONS` or `DBA_LOAD_OPERATIONS`,
- `LOGFILE_TABLE`,
- `BADFILE_TABLE`.

## Iceberg external table on OCI Object Storage

Minimum inputs for direct metadata mode:

- `external_table_name`
- `credential_name`
- exact OCI Object Storage URI for the Iceberg root `metadata.json`

Minimum inputs for HadoopCatalog on OCI:

- `external_table_name`
- `credential_name`
- OCI Object Storage lakehouse folder URI
- `iceberg_table_path`, for example `<database>.<table>`

Before generating the final `DBMS_CLOUD.CREATE_EXTERNAL_TABLE`, run or generate:

- table existence check for the external table name,
- object discovery if the user provides a folder or prefix instead of an exact `metadata.json`,
- optional ACL check or ACL helper for `objectstorage.<region>.oraclecloud.com`,
- a warning that Iceberg external table creation is mutating and creates query access, not a `COPY_DATA` load.
