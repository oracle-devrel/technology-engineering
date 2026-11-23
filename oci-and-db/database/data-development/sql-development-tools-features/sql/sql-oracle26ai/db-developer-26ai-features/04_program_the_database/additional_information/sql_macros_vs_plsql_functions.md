# SQL Macros vs. PL/SQL Functions

> **Developer question:** I already encapsulate logic in PL/SQL functions. What problem does a SQL macro solve, and is it worth learning?

## 1. What is the new capability?

A **SQL macro is a reusable SQL template**, defined using familiar `CREATE FUNCTION` syntax. Rather than returning a computed business value, its body returns **SQL text** that Oracle expands into the calling SQL statement. There are two forms: **scalar macros** (reusable expressions) and **table macros** (reusable queries usable in `FROM`).

**Mental model:** a conventional function is *called to do work*; a SQL macro is *expanded to describe SQL work*. A table macro is especially useful when a view is too fixed and repeating a complex query with different parameters is becoming hard to maintain.

## 2. How did we solve this before?

A PL/SQL function can compute a result from each row, or developers can copy SQL between reports, create a view, or use a parameterized application query. Functions are excellent for procedural logic, but a scalar function call can obscure its implementation from the SQL optimizer. A view exposes SQL to the optimizer, but cannot directly accept parameters like a function.

```sql
-- Ordinary procedural function: returns a value.
CREATE OR REPLACE FUNCTION net_price_fn(
    p_amount NUMBER, p_discount_pct NUMBER
) RETURN NUMBER IS
BEGIN
    RETURN p_amount * (1 - p_discount_pct / 100);
END;
/
SELECT net_price_fn(200, 10) AS price FROM dual; -- 180
```

## 3. What is different?

A scalar macro returns a **SQL expression**, not the result `180`:

```sql
CREATE OR REPLACE FUNCTION net_price_sql(
    p_amount NUMBER, p_discount_pct NUMBER
) RETURN VARCHAR2 SQL_MACRO(SCALAR) IS
BEGIN
    RETURN 'p_amount * (1 - p_discount_pct / 100)';
END;
/
SELECT net_price_sql(200, 10) AS price FROM dual; -- 180
```

Oracle expands the macro into the invoking SQL, conceptually like writing `SELECT 200 * (1 - 10/100) ...`. The arguments in the returned text refer to **macro parameter names**; do not concatenate user input into SQL text. **Important 26ai nuance:** Oracle's SQL Transpiler can automatically convert *eligible ordinary PL/SQL functions* to SQL expressions too. Therefore, scalar macros are **not automatically faster** than PL/SQL functions; test the actual plan and workload.

**More compelling coaching example — parameterized reusable query:**

```sql
-- Assumes an existing SALES(order_id, customer_id, amount, status) table.
CREATE OR REPLACE FUNCTION sales_above(p_min_amount NUMBER)
    RETURN VARCHAR2 SQL_MACRO(TABLE) IS
BEGIN
    RETURN q'{SELECT order_id, customer_id, amount
              FROM sales
              WHERE status = 'OPEN'
                AND amount >= sales_above.p_min_amount}';
END;
/

SELECT customer_id, SUM(amount) AS open_value
FROM sales_above(1000)
GROUP BY customer_id;
```

**What to point out:** `sales_above(1000)` reads like a parameterized view, yet the calling query can still filter, join, group, and aggregate the exposed relational rows. The optimizer works with the expanded query. A conventional scalar PL/SQL function does not naturally return a composable SQL table expression in this way.

## 4. What are the advantages and limitations?

| SQL macros help when… | Stay with functions or other SQL when… |
|---|---|
| Several reports repeat a complicated, parameterized query. | Logic is procedural, performs side effects, or must be called directly from PL/SQL. |
| You want reusable SQL expressions or relational query building blocks. | A simple view or SQL expression is already clear enough. |
| You want optimizer visibility into generated SQL. | An eligible PL/SQL function is already transpiled efficiently in 26ai. |

**Trade-offs:** returned SQL must be valid; expansion and privileges deserve testing. Table macros belong in `FROM`; scalar macros cannot be used as table expressions. SQL macros have restrictions (for example, no use in function-based indexes or virtual-column expressions). Calling a macro *from PL/SQL* does not expand it as SQL; it behaves as a text-returning function. A macro is **not** a general-purpose replacement for PL/SQL.

## 5. When should developers adopt it?

**Learn table SQL macros first** if you maintain complex reporting SQL, reusable filtering/aggregation logic, or repeated queries that differ mainly by parameters. They offer a practical capability that a fixed view and a conventional scalar function do not combine. **Learn scalar macros selectively** for reusable SQL expressions; in 26ai, benchmark against ordinary functions because of SQL Transpiler improvements. Keep PL/SQL for orchestration, procedural business rules, exception handling, and APIs.

**Live coaching prompt:** “If I want a reusable, parameterized *query* that callers can still join and aggregate, would a function returning a number solve it?” No — that is the stronger SQL macro use case.

## Key takeaway

**A PL/SQL function encapsulates execution; a SQL macro encapsulates SQL that becomes part of the caller's statement.** The strongest reason to learn macros is **composable, parameterized SQL**, not an unqualified performance promise.

## Documentation — Oracle AI Database 26ai

- [SQL macros — PL/SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/26/lnpls/SQL_MACRO-clause.html)
- [CREATE FUNCTION — SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/CREATE-FUNCTION.html)
