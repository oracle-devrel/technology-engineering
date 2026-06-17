# Example: List objects before loading

User request:

> In bucket `raw-data`, list files under `sales/2026/04/` and decide what to load.

Recommended flow:

1. Generate or execute `LIST_OBJECTS`.
2. Filter out markers/control files.
3. Group by extension and naming pattern.
4. Ask for confirmation if files are mixed.
5. Generate exact URI list or wildcard/regex pattern.

```sql
select object_name,
       bytes,
       checksum,
       created,
       last_modified
from dbms_cloud.list_objects(
  credential_name => 'OBJ_STORE_CRED',
  location_uri    => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/raw-data/o/sales/2026/04/'
)
order by object_name;
```
