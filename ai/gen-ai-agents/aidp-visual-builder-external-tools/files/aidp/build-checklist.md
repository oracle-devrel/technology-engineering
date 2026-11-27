# Build checklist

- [ ] Select AI profile is scoped to the intended tables and a natural-language query works.
- [ ] Autonomous Database MCP server is enabled and exposes `SUPPLIER_FEEDBACK_SQL` with `ACTION` and `QUERY`.
- [ ] AIDP database credential contains the required username/password keys; no values are in source.
- [ ] OCI Generative AI API key has file and vector-store permissions in the selected project/compartment.
- [ ] Vector store contains uploaded files and the file batch is completed.
- [ ] Direct vector-store search returns a relevant passage.
- [ ] AIDP egress and Credential Store support both database and vector-search calls.
- [ ] Select AI Custom Tool and Vector Store HTTP tool are attached to the same agent.
- [ ] Database-only, document-only, and combined Playground questions work.
- [ ] Combined trace shows both tools and the answer matches their results.
- [ ] Deployed endpoint works with the intended caller identity.
- [ ] Native AIDP Git Bundle exported if sharing the actual visual flow.
