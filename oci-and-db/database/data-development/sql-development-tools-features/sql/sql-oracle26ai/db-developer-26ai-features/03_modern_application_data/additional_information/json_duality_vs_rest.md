# JSON Relational Duality Views vs. Handwritten REST/JSON Mapping

> **Developer question:** Our ORDS service already returns JSON. What is the point of a JSON Relational Duality View?

## 1. What is the new capability?

A **JSON Relational Duality View** declares how one or more relational tables appear as a JSON document, and—when authorized in its definition—how document writes map back to those tables. Relational rows remain the source of truth; the view is not a second JSON copy. Its document metadata can support content-based optimistic concurrency checks.

## 2. How did we solve this before?

An ORDS handler or application service selects rows, assembles JSON, validates incoming payloads, and writes changes to the relevant tables. That works, but the read and write mappings can diverge as a schema evolves.

```sql
CREATE TABLE dv_customer (id NUMBER PRIMARY KEY, name VARCHAR2(80));
INSERT INTO dv_customer VALUES (1, 'Alice');
COMMIT;

-- Traditional read mapping; write mapping is separate application code.
SELECT JSON_OBJECT('id' VALUE id, 'name' VALUE name) AS doc
FROM dv_customer WHERE id = 1;
```

## 3. What is different?

```sql
-- Simple one-table illustration; UPDATE is explicitly permitted.
CREATE OR REPLACE JSON RELATIONAL DUALITY VIEW customer_dv AS
  SELECT JSON {'_id': c.id, 'name': c.name}
  FROM dv_customer c WITH UPDATE;

SELECT JSON_SERIALIZE(data PRETTY) FROM customer_dv;
```

**Show the document:** a result resembles `{ "_id": 1, "name": "Alice", "_metadata": { ... } }`. The view defines the document shape. A JSON-producing `SELECT` does not, by itself, provide a governed reverse mapping for updates.

**API coaching walkthrough (illustrative, not a preconfigured ORDS route):**

```http
GET /ords/demo/customer_dv/1
Accept: application/json
```

A client receives the document and its current ETAG. The client edits `name` and submits a full replacement with the original ETAG. If another writer changed checked content meanwhile, the database rejects the stale replacement; a properly configured HTTP layer may surface this as `412 Precondition Failed`. The client re-reads and resolves the conflict. **The actual URL, HTTP method, and payload depend on how ORDS exposes the view.**

**Important distinction:** The duality view is the **data/document mapping**; ORDS is the **HTTP transport/API**. You can expose a duality view through ORDS, but creating the view does not automatically create a production REST API, authentication, routing, or business workflow. A duality view is read-only by default unless write permissions are declared.

## 4. What are the advantages and limitations?

| Advantage | Qualification |
|---|---|
| Declarative JSON mapping over relational data | Requires keys, supported mapping shape and write annotations |
| Database-governed document updates | Not a replacement for service orchestration or external API contracts |
| ETAG-aware document replacement | Client must preserve/reconcile versions; partial updates differ |
| Multiple document views over relational source | Model changes and authorization need careful review |

## 5. When should developers adopt it?

**Adopt** when the application wants a document-shaped CRUD interface while preserving relational storage, SQL access, and database-managed write rules. **Keep custom ORDS handlers/services** for workflows spanning multiple operations, external integrations, specialized contracts, and logic not represented by a document update. The two approaches commonly work together.

## Key takeaway

**A duality view can replace hand-written document-to-relational mapping; it does not replace ORDS or the application service layer.**

## Documentation — Oracle AI Database 26ai

- [CREATE JSON RELATIONAL DUALITY VIEW](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-json-relational-duality-view.html)
- [JSON_OBJECT](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/JSON_OBJECT.html)
