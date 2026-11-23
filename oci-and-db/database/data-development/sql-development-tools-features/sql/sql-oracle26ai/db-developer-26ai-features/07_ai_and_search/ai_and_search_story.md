# AI & Search

## Presenter purpose
Help SQL developers understand why semantic retrieval matters, what embeddings contribute, and how Oracle keeps search close to structured application data. Avoid implying that vector search requires a generative AI model.

## Introduction — why developers should care
Keyword search is excellent when a user knows the exact product name, error code, or phrase. But a customer may describe a problem using different words from the documentation. Semantic search looks for **similar meaning** rather than identical wording; hybrid search combines that flexibility with precise lexical matching.

This creates opportunities in support knowledge bases, product documentation, incident search, and enterprise application search, especially when results must also respect business filters and permissions.

## The capabilities and what to notice

### Embeddings and VECTOR — represent meaning
An embedding model converts content and a query into compatible numeric vectors. Oracle stores them in `VECTOR` columns. `VECTOR_DISTANCE` ranks nearby representations; the model defines what similarity means. Embeddings are **not** created automatically by declaring a VECTOR column, and a large language model is not required simply to retrieve similar content.

### Vector indexes — scale retrieval
As a corpus grows, approximate vector indexes can reduce the cost of similarity retrieval, with accuracy/latency trade-offs to evaluate on real data. The right index and search configuration depend on corpus size, workload, and recall requirements.

### Hybrid search — meaning plus exact terms
Pure semantic similarity may overlook an exact product identifier, error code, or required phrase. Hybrid search combines lexical and semantic signals, allowing application search to use both. SQL predicates, joins, and existing data relationships remain important for narrowing results to the right business context.

### In-database embedding generation — optional model placement
A compatible ONNX embedding model can be imported and invoked from SQL or PL/SQL. This can avoid a separate inference call, but shifts model deployment, resource usage, and lifecycle management to the database. External embedding services remain an option. The key is using compatible embeddings for stored content and incoming queries.

## Demo coaching
`ai_and_search_demo.sqlnb` uses **prepared vectors** to isolate retrieval mechanics from model setup. Show similarity ranking and the vector-index concept, then explain why hybrid retrieval matters. The small vectors are teaching aids; they are not a production semantic benchmark. The optional `in_database_embeddings/` notebook explores importing and using an ONNX model.

If someone asks about RAG, distinguish retrieval from generation: a later application can pass retrieved context to an LLM, but that is a separate design choice.

## Close-out — the memorable point
Applications can search by meaning and still combine results with SQL and business data. The developer gets a richer search option without automatically introducing a separate vector-only data silo. Start with a search experience where users routinely know the problem but not the exact wording.

**Assets:** `ai_and_search_demo.sqlnb`, `ai_and_search_cleanup.sql`; optional `in_database_embeddings/in_database_embeddings.sqlnb`.
