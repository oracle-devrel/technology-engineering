# Select AI in simple terms

Select AI lets a database turn a plain-language question into a database query using a configured profile. The profile tells it which tables and columns it may use and which model settings apply. The database runs the query and returns rows.

In this pattern, the agent sends the user’s question to the Select AI tool. The tool returns database results; the agent then explains those results in plain language. A database profile and database account determine what data is accessible. Keep the profile narrow and use read-only access for an analytics agent.

Select AI is for structured records. It does not search policy documents by meaning. Use a RAG/vector search tool for those documents, then let the agent combine the two results when the question needs both.

A custom function can do other bounded tasks such as formatting data, checking required fields, or building a structured result. A function that changes records needs stronger access controls, logging, and approval. The included Custom Tool only reads database results.
