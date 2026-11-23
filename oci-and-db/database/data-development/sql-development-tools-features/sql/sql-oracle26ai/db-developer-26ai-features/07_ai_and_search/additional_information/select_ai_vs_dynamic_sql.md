# Select AI vs. Application-Generated Dynamic SQL

> **Developer question:** We can already generate SQL using bind variables and query builders. Why introduce Select AI?

## 1. What is the new capability?

**Select AI** uses an LLM and a configured AI profile to interpret natural-language questions and generate SQL from permitted database context. It is intended for open-ended discovery, not to replace predictable SQL in transactional application code.

## 2. How did we solve this before?

Developers explicitly implement permitted questions as SQL, parameterized reports, query builders, or PL/SQL dynamic SQL. The meaning is deterministic because the application author defines it.

```sql
-- Assumes demo_orders(region, amount, status, order_date).
SELECT region, SUM(amount) AS total_sales
FROM demo_orders
WHERE status = 'COMPLETE'
GROUP BY region;
```

## 3. What is different?

```sql
-- Requires a configured Select AI profile and permitted objects.
SELECT AI SHOWSQL total completed sales by region;
```

**Coaching walkthrough:** Ask the audience to change the question to “completed sales by region for last quarter, excluding returns.” A fixed report needs explicit changes or parameters; Select AI can attempt to translate the new request into SQL. Use `SHOWSQL` first and inspect the generated statement. Does it understand what counts as a return? Which date defines “last quarter”? Does it use the approved measure of sales? **Natural language does not resolve business ambiguity by itself.**

**Runtime distinction:** Conventional dynamic SQL builds a query from known rules, then Oracle executes it. Select AI first asks a model to interpret intent, so generated SQL can differ or be incorrect. `SHOWSQL` is a safer teaching mode than executing the model's first answer. Data exposure to an AI provider, object allowlists, privileges, and cost controls must be planned.

## 4. What are the advantages and limitations?

| Select AI | Deterministic dynamic SQL |
|---|---|
| Flexible questions without a new UI for each report | Stable, tested application contracts |
| Accessible to analysts using business language | Explicit predicates, binds and allowed query shapes |
| Needs prompt/context governance and SQL review | Requires development effort for each supported intent |
| LLM may misunderstand business semantics | Easier to regression-test and audit |

## 5. When should developers adopt it?

**Adopt** for governed ad hoc exploration where a human can inspect and correct results. **Keep explicit SQL** for billing, financial controls, transactional decisions and contractual reports. A useful hybrid is to prototype analytical questions with Select AI, then promote validated SQL into a conventional report.

## Key takeaway

**Dynamic SQL automates a query the developer understands; Select AI attempts to infer a query from a user's intent.**

## Documentation — Oracle AI Database 26ai

- [Use AI keyword to enter prompts](https://docs.oracle.com/en/database/oracle/oracle-database/26/selai/use-ai-keyword-enter-prompts.html)
- [Native dynamic SQL](https://docs.oracle.com/en/database/oracle/oracle-database/26/lnpls/native-dynamic-sql.html)
