# AI Vector Search vs. Oracle Text

> **Developer question:** Oracle Text already searches documents. What new problem does AI Vector Search solve?

## 1. What is the new capability?

**AI Vector Search** stores and compares embedding vectors: numerical representations of text, images or other content produced by an embedding model. A similarity query can retrieve semantically related items even when they do not share exact words. Oracle Text remains a full-text/linguistic search capability.

## 2. How did we solve this before?

With Oracle Text, developers index document text and query words, phrases, and supported linguistic operators. This is excellent for precise terms, legal phrases, identifiers and explainable matches.

```sql
-- Assumes docs(id, body) and a suitable Oracle Text index on body.
SELECT id, body FROM docs
WHERE CONTAINS(body, 'car') > 0;
```

## 3. What is different?

```sql
-- Assumes docs also has embedding VECTOR, created by a chosen model.
-- :query_vector must be generated with the same compatible model.
SELECT id, body
FROM docs
ORDER BY VECTOR_DISTANCE(embedding, :query_vector, COSINE)
FETCH FIRST 5 ROWS ONLY;
```

**Coaching scenario:** Document A says “car insurance renewal”; document B says “automobile policy extension.” Ask which result a keyword search for `car` returns. Then ask what a semantic search for “renew my vehicle coverage” might rank. A well-chosen embedding can connect the concepts without matching words. It is **not guaranteed**: relevance depends on the model, domain vocabulary, chunking, and evaluation data.

**Runtime walkthrough:** Text search evaluates an indexed textual query. Vector search first needs embeddings for stored content and the user's query, then computes/ranks distances (possibly with an approximate vector index). Show the top results and ask whether the similarity ordering is actually useful; a numerical distance is not a factual correctness score.

## 4. What are the advantages and limitations?

| AI Vector Search | Oracle Text |
|---|---|
| Semantic similarity and concept discovery | Precise keyword, phrase and linguistic search |
| Requires embedding generation and model lifecycle | Requires text index and query-language design |
| Approximate indexes may trade recall for speed | Lexical match behavior is often easier to explain |
| Can retrieve related but nonmatching terms | Strong for exact identifiers and compliance wording |

Hybrid retrieval can combine lexical precision with semantic recall; neither is a universal replacement for the other.

## 5. When should developers adopt it?

**Use vectors** for natural-language discovery, recommendations and retrieval-augmented generation where semantic relevance matters. **Use Oracle Text** for exact wording, filters and transparent lexical matching. **Combine** when users need both; evaluate quality with representative queries before committing to an embedding model or index design.

## Key takeaway

**Oracle Text asks “which words match?”; AI Vector Search asks “which items are close in meaning?”**

## Documentation — Oracle AI Database 26ai

- [AI Vector Search User's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/26/vecse/)
- [Oracle Text Reference](https://docs.oracle.com/en/database/oracle/oracle-database/26/ccref/)
