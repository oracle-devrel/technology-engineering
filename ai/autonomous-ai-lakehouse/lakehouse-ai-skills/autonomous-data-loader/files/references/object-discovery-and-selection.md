# Object discovery and selection

Use this reference when the user gives a bucket, folder, or prefix instead of exact files.

## Contents

- Discovery query
- Selection rules
- Choosing exact files versus patterns
- Header sampling for CSV with GET_OBJECT
- Fallback when sampling is unavailable

## Discovery query

Run `DBMS_CLOUD.LIST_OBJECTS` before choosing files from a bucket or prefix.

```sql
select object_name,
       bytes,
       checksum,
       created,
       last_modified
from dbms_cloud.list_objects(
  credential_name => '<CREDENTIAL_NAME>',
  location_uri    => '<OCI_OBJECT_STORAGE_BUCKET_OR_PREFIX_URI>'
)
order by last_modified desc;
```

Use this as read-only in MCP-enabled mode.

## Selection rules

- Do not guess blindly from a bucket or prefix.
- Prefer exact file lists for a small number of selected files.
- Prefer wildcard or regex patterns only when files are homogeneous.
- Do not mix formats in one `COPY_DATA` operation.
- Exclude marker/control files such as `_SUCCESS`, `.crc`, manifests, readme files, and zero-byte files unless explicitly requested.
- If the prefix contains multiple datasets, ask the user which dataset to load.
- If file extensions and naming patterns are inconsistent, ask for confirmation before loading.

## Choosing exact files versus patterns

For a small list of selected objects, generate explicit URIs:

```sql
file_uri_list => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/path/file1.csv,
                  https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/path/file2.csv'
```

For a homogeneous folder, a wildcard pattern may be clearer:

```sql
file_uri_list => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/raw/sales/*.csv'
```

For more complex matching, use `regexuri` in the `format` argument and make the regex explicit.

```sql
format => json_object(
  'type' value 'csv',
  'regexuri' value 'true',
  'skipheaders' value 1,
  'enablelogs' value 'true',
  'logretention' value 7
)
```

## Header sampling for CSV with GET_OBJECT

If the user wants conservative CSV staging and the environment can execute SQL, use `DBMS_CLOUD.GET_OBJECT` to read an initial byte range from one representative CSV file. Extract the first record line as the header.

Example pattern:

```sql
select to_clob(
         dbms_cloud.get_object(
           credential_name => '<CREDENTIAL_NAME>',
           object_uri      => '<CSV_OBJECT_URI>',
           startoffset     => 0,
           endoffset       => 65535
         )
       ) as sample_text
from dual;
```

Use this cautiously:

- It is a sampling helper, not a full parser.
- It is best for uncompressed text CSV files.
- If the object is compressed, encrypted, uses an unexpected character set, or cannot be converted cleanly to text, ask the user to provide the header line instead of guessing.
- It may need adjustment for encoding, compressed files, or headers longer than the sampled range.
- If embedded newlines appear in quoted fields, the first physical line may still be the header, but do not assume later records are simple.
- Use the header only for staging column names, not for final business typing.

## Fallback when sampling is unavailable

If the assistant cannot read the object through MCP, ask the user to paste the header line or provide a schema. Do not invent column names from the filename or prefix.
