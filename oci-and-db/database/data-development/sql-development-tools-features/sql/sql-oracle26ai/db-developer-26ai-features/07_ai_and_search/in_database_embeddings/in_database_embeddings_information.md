# In-Database Embeddings with an Imported ONNX Model

## Scope

This optional material covers the database-resident embedding path within the AI & Search section. It covers importing a compatible ONNX embedding model into Oracle AI Database 26ai, verifying the registered model, generating embeddings from SQL and PL/SQL, storing embeddings with application data, and using those vectors for semantic retrieval.

It does not cover general LLM generation, external embedding providers, model training, or production model governance.

## Developer problem

Semantic search needs an embedding model to convert text into vectors. With an external model, the application or an integration service calls the model and moves the resulting vector back to the database.

Oracle can instead host a compatible embedding model in the database. In that architecture, the database can generate embeddings next to the application data and use the same model for stored content and query text.

## Who needs to be involved

### Database administrator / cloud database administrator

The administrator or platform owner is responsible for the database and model-import prerequisites, including the database version, compatibility setting, model storage location, directory access, and any required resource configuration.

For Autonomous AI Database, the administrator or environment owner also needs to provide a supported Object Storage access path and ensure that the target database has the required database privileges.

### Database developer / schema owner

The developer owns the database objects and code that use the model: loading the model after the environment is prepared, checking its metadata, calling the embedding APIs, storing vectors, and using them in application queries.

### Application / AI team

The application team selects or supplies an appropriate embedding model and must ensure that the same embedding model and configuration are used consistently for stored content and query text. Model selection, quality evaluation, chunking strategy, and production lifecycle remain application/AI concerns.

## Platform and database prerequisites

1. Use an Oracle AI Database 26ai environment with the Vector features available. Oracle documents a minimum `COMPATIBLE` value of `23.4.0` for the relevant Vector functionality.
2. The imported model must be a supported ONNX embedding model with the input/output contract required by Oracle's embedding inference APIs.
3. For Autonomous AI Database, use the documented database-managed directory and Object Storage retrieval path, or another supported model-loading path for the target environment.
4. The database schema needs the privileges required to use the model-loading and Vector APIs. The consolidated developer setup script prepares the normal demo schema privileges.
5. Vector Pool sizing is an environment consideration when the workflow also creates vector indexes. Do not change database memory automatically as part of a presentation setup.

## Autonomous Always Free considerations

Autonomous AI Database Always Free provides limited storage. The database-resident model, application tables, vector indexes, and any objects left behind by repeated notebook runs consume the same storage budget.

Keep the imported model and demonstration corpus deliberately small, and run the separate cleanup scripts between sessions. Avoid accumulating additional vector indexes or duplicate model objects.

For current limits, use the Oracle Autonomous AI Database Always Free documentation rather than relying on a fixed value embedded in the notebook material.

## Model import flow

For an Autonomous AI Database Object Storage workflow:

1. Make the ONNX model available from Object Storage using the documented access mechanism.
2. Retrieve the model file into the database directory with `DBMS_CLOUD.GET_OBJECT` when using the documented directory workflow.
3. Import the ONNX model with `DBMS_VECTOR.LOAD_ONNX_MODEL`.
4. Verify the model through the database model metadata views.
5. Use the registered model from SQL and PL/SQL.

The exact Object Storage URL, credential, directory name, and model file are environment-specific and must not be hard-coded into shared presentation scripts.

## Database-side APIs

- `DBMS_CLOUD.GET_OBJECT` retrieves a model file into a database directory for supported Autonomous workflows.
- `DBMS_VECTOR.LOAD_ONNX_MODEL` registers the imported model in the database.
- `VECTOR_EMBEDDING` generates embeddings in SQL.
- `DBMS_VECTOR.UTL_TO_EMBEDDING` supports embedding generation from PL/SQL-oriented workflows.
- `VECTOR_DISTANCE` supports similarity comparison.

Oracle documents a 4000-character limit for a single text input to `UTL_TO_EMBEDDING`; longer application documents should be chunked before embedding.

## Storage and model lifecycle

An imported model is a database-managed dependency. The database developer should understand where the model is stored, how it is versioned, and how applications remain consistent when the model changes.

The embedding model and its configuration should be treated as part of the application's data pipeline, not as an incidental notebook object.

## External embedding providers

Oracle also supports embedding generation through third-party model services. That path introduces provider credentials, network access, provider configuration, and the requirement to use a consistent embedding model for stored data and query text.

This optional material demonstrates the in-database path so that developers can compare the architectural trade-off with an external provider.

## Assets

Notebook: `in_database_embeddings.sqlnb`
Cleanup: `in_database_embeddings_cleanup.sql`

## References

### Oracle documentation

- https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/import-onnx-models-oracle-ai-database-end-end-example.html
- https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/sql-quick-start-using-vector-embedding-model-uploaded-database.html
- https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/convert-text-string-embedding-oracle-ai-database.html
- https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/dbms_vector-vecse.html
- https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/inmemory_onnx_model-dbms_vector.html
- https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/select-ai-examples.html
- https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-always-free.html
- https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/autonomous-database-for-developers.html

### Oracle practitioner material

- https://blogs.oracle.com/developers/how-to-load-embedding-models-into-oracle-ai-database-in-2026
- https://blogs.oracle.com/developers/building-onnx-embedding-workflows-in-oracle-ai-database-with-python
- https://blogs.oracle.com/database/getting-started-with-oracle-database-23ai-ai-vector-search
