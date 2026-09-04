# Version notes

## v0.1

Initial public-oriented version of Autonomous AI Lakehouse Data Loader.

Scope:

- OCI Object Storage as source.
- Oracle Autonomous AI Lakehouse as target.
- `DBMS_CLOUD.LIST_OBJECTS` for object discovery.
- `DBMS_CLOUD.GET_OBJECT` for optional CSV header sampling.
- `DBMS_CLOUD.COPY_DATA` for relational-table loads.
- `DBMS_CLOUD.COPY_COLLECTION` for JSON/SODA collection loads.
- Native load monitoring through `USER_LOAD_OPERATIONS` and `DBA_LOAD_OPERATIONS`.
- Log and badfile troubleshooting.
- Conservative CSV staging and post-load profiling.
- Apache Iceberg query access for data stored in OCI Object Storage using documented direct `metadata.json` and HadoopCatalog patterns with `DBMS_CLOUD.CREATE_EXTERNAL_TABLE`.
- MCP-first execution with generate-only fallback.
- No scripts bundled.
