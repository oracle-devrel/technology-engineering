# Modern Application Data

## Presenter purpose
Explain how one relational source can serve application-shaped JSON and graph-style relationship questions. Keep **JSON Relational Duality**, **GraphQL-style definitions**, and **SQL/PGQ** distinct: similar-sounding names, different jobs.

## Introduction — why developers should care
An application developer may want a customer document containing nested orders, while a database developer wants keys, constraints, SQL, and transactions. Traditionally, the API layer has to assemble the document and map updates back to tables, or the organization maintains another document copy. A Duality View makes the document shape a database definition over the existing relational data.

## The capabilities and what to notice

### JSON Relational Duality Views — a document over relational truth
A Duality View presents related rows as hierarchical JSON. A customer can contain an `orders` array while the underlying records remain in customer and order tables. Supported document inserts, updates, and deletes are mapped back to the tables according to the view definition and database constraints. This is more than JSON generation: it can be an **updatable document interface**.

### SQL or GraphQL-style definition — two authoring approaches
A database developer can define the document using SQL `SELECT JSON` and nested subqueries. Oracle also supports a GraphQL-style definition that describes the desired hierarchy and permitted operations more declaratively, using relationships available from relational metadata. Both create the same kind of Duality View and use the same underlying update mechanism. This provides a shared vocabulary for a JSON/API developer and a SQL developer discussing the document contract.

GraphQL originated as an API query language, but **GraphQL-style DDL is not a general-purpose GraphQL query endpoint**. Application-facing GraphQL queries still require an appropriate API layer. It is also **not SQL/PGQ**.

### Property Graph Views and SQL/PGQ — query connections
Property graphs model vertices and edges over data; SQL/PGQ expresses relationship patterns and traversals. For example, a developer can ask how customers, accounts, and transfers connect. This is relationship analysis, not a different spelling of GraphQL or a way of defining a customer JSON document.

### JSON Schema — a complementary document contract
For data stored natively as JSON, schema validation can constrain the allowed document structure. It complements Duality Views rather than replacing relational constraints beneath them.

## Demo coaching
`modern_application_data_demo.sqlnb` creates customer/order tables and two Duality Views: one SQL-defined and one GraphQL-defined. The walkthrough compares the resulting JSON documents, dictionary metadata, and the effect of an underlying relational update. Read the nested customer document, then change relational data and observe the JSON representation. The notebook also introduces JSON Schema validation. Explain the **update capability** as a property of appropriately configured Duality Views, without implying that this notebook demonstrates every write path or a GraphQL API.

If someone asks about concurrency, JSON Duality Views can use ETAG-based optimistic concurrency control for supported document updates; that is separate from Lock-Free Reservations.

## Close-out — the memorable point
Developers can agree on a useful JSON document shape without surrendering relational integrity or duplicating business data. SQL and GraphQL-style definitions are alternative ways to declare that document; SQL/PGQ answers a different question about relationships. Choose the access shape that fits the application, not another storage silo by default.

**Metadata comparison:** Compare object type, `DATA` column metadata and JSON document equivalence. SQL and GraphQL view definitions need not have identical DDL text; update capabilities must be specified deliberately.

**Assets:** `modern_application_data_demo.sqlnb`, `modern_application_data_cleanup.sql`.


## SQL and GraphQL Duality View comparison

The notebook creates SQL-defined and GraphQL-defined Duality Views over the same relational customer and order tables, then runs the same `JSON_SERIALIZE` document query against both views. This focuses on equivalent application-facing results, not dictionary metadata inspection or redundant relational updates.
