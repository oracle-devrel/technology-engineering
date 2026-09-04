# Example: CSV conservative staging

User request:

> There is a CSV in this bucket. I do not have a table. Load it.

Recommended response:

- Explain that CSV does not provide reliable types.
- List objects first.
- Read or ask for the header.
- Ask the user for a staging table name.
- Create a staging table with all CSV columns as `VARCHAR2(4000)`.
- Load with `COPY_DATA` and `skipheaders => 1`.
- Profile after load.

Assume header:

```text
order_id,customer_id,order_date,amount,currency
```

Proposed staging table:

```sql
create table STG_SALES_CSV (
  ORDER_ID    varchar2(4000),
  CUSTOMER_ID varchar2(4000),
  ORDER_DATE  varchar2(4000),
  AMOUNT      varchar2(4000),
  CURRENCY    varchar2(4000)
);
```

Load:

```sql
declare
  l_operation_id number;
begin
  dbms_cloud.copy_data(
    table_name      => 'STG_SALES_CSV',
    credential_name => 'OBJ_STORE_CRED',
    file_uri_list   => 'https://objectstorage.<region>.oraclecloud.com/n/<namespace>/b/<bucket>/o/raw/sales/sales.csv',
    format          => json_object(
      'type' value 'csv',
      'skipheaders' value 1,
      'delimiter' value ',',
      'quote' value '"',
      'blankasnull' value 'true',
      'rejectlimit' value 100,
      'enablelogs' value 'true',
      'logretention' value 7
    ),
    operation_id    => l_operation_id
  );
  dbms_output.put_line('operation_id=' || l_operation_id);
end;
/
```

Post-load profiling:

```sql
select count(*) as row_count from STG_SALES_CSV;

select
  max(length(ORDER_ID)) as order_id_max_len,
  max(length(CUSTOMER_ID)) as customer_id_max_len,
  max(length(CURRENCY)) as currency_max_len
from STG_SALES_CSV;
```
