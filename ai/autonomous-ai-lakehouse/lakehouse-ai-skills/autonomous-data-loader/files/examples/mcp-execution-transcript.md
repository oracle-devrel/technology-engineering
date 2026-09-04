# Example: MCP-assisted object discovery and load planning

This example shows the expected behavior when an MCP SQL execution tool is available.

## User prompt

List the files under this Object Storage prefix and help me decide what to load:

- credential: `OBJ_STORE_CRED`
- URI: `https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/example_ns/b/raw-data/o/sales/2026-04-24/`

## Assistant behavior

The assistant may execute a read-only discovery query through MCP:

```sql
select object_name,
       bytes,
       checksum,
       created,
       last_modified
from dbms_cloud.list_objects(
  credential_name => 'OBJ_STORE_CRED',
  location_uri    => 'https://objectstorage.eu-frankfurt-1.oraclecloud.com/n/example_ns/b/raw-data/o/sales/2026-04-24/'
)
order by last_modified desc;
```

## Example tool result

```text
raw/sales/2026-04-24/sales_001.csv    1048576
raw/sales/2026-04-24/sales_002.csv    2097152
raw/sales/2026-04-24/_SUCCESS         0
raw/sales/2026-04-24/readme.txt       1024
```

## Assistant follow-up

The prefix contains two CSV data files plus marker/documentation files. I recommend loading only the CSV files and excluding `_SUCCESS` and `readme.txt`.

Before generating `COPY_DATA`, I need either:

1. an existing target table, or
2. approval to create a conservative staging table from the CSV header.

If conservative staging is approved and MCP can sample the file, the assistant may use `DBMS_CLOUD.GET_OBJECT` to read the header from one representative CSV file.
