# Native JSON Data Type vs. CLOB with JSON Validation

> **Developer question:** A `CLOB CHECK (payload IS JSON)` works. Why switch to the native JSON type?

## 1. What is the new capability?

The native `JSON` SQL type stores JSON in Oracle's binary JSON representation (OSON), rather than treating the document primarily as text. It is intended for JSON data that the database reads, navigates, indexes, or updates as a document.

## 2. How did we solve this before?

A CLOB holds serialized text. `IS JSON` validates syntax but does not change the underlying text storage.

```sql
CREATE TABLE event_text (
  id NUMBER PRIMARY KEY,
  payload CLOB CONSTRAINT event_text_json CHECK (payload IS JSON)
);
INSERT INTO event_text VALUES (1, '{"kind":"login","count":2}');
```

## 3. What is different?

```sql
CREATE TABLE event_native (id NUMBER PRIMARY KEY, payload JSON);
INSERT INTO event_native VALUES (1, JSON('{"kind":"login","count":2}'));

SELECT JSON_VALUE(payload, '$.kind') AS kind FROM event_text;
SELECT JSON_VALUE(payload, '$.kind') AS kind FROM event_native;
```

**Coaching sequence:** The SQL queries look almost identical. Ask: *What changed if the query did not?* Answer: storage and the database's JSON-processing representation. The CLOB contains textual serialization; native JSON stores the parsed document in OSON. In a workload that repeatedly navigates or updates document fields, that can matter more than the syntax of `JSON_VALUE`.

**Practical decision test:** If you must preserve the exact incoming JSON bytes, whitespace, or original textual formatting for audit/signature purposes, native JSON is not a substitute for retaining the original text. If you need document semantics and efficient processing, native JSON is the better candidate. Benchmark actual data and operations; do not promise a universal speedup.

## 4. What are the advantages and limitations?

| Native JSON | Validated CLOB |
|---|---|
| Binary JSON representation for JSON processing | Preserves original textual payload when stored unchanged |
| Suitable for JSON-oriented operations and indexing | Useful for text-based interchange or archival contracts |
| Requires compatible drivers and migration planning | May incur repeated parsing costs for JSON-heavy workloads |

Both support many SQL/JSON queries. Native JSON does not automatically improve a poor data model or make every JSON operation faster.

## 5. When should developers adopt it?

**Prefer native JSON** for new document-centric application data with frequent JSON access. **Retain CLOB** when exact source serialization is part of the business requirement or client migration is prohibitive. A system can retain raw payloads separately while also storing parsed JSON for operational queries.

## Key takeaway

**`IS JSON` checks that text is valid JSON; the `JSON` type tells Oracle to store and work with it as JSON.**

## Documentation — Oracle AI Database 26ai

- [JSON data type](https://docs.oracle.com/en/database/oracle/oracle-database/26/adjsn/json-data-type.html)
- [IS JSON condition](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/IS-JSON-Condition.html)
