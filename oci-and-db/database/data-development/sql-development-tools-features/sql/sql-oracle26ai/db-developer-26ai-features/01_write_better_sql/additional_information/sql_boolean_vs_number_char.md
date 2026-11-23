# SQL BOOLEAN vs. NUMBER(1) / CHAR(1)

> **Developer question:** We have stored flags as `0/1` or `Y/N` for years. What does a SQL `BOOLEAN` actually buy us?

## 1. What is the new capability?

SQL `BOOLEAN` represents `TRUE`, `FALSE`, and `NULL` directly in a table or SQL expression. It closes a long-standing distinction: PL/SQL had Boolean variables, but older Oracle SQL schemas commonly encoded flags in numbers or characters. **The advantage is a type-level contract, not a speed claim.**

## 2. How did we solve this before?

A numeric flag needs an agreed encoding and usually a constraint. Otherwise `active = 7` is technically valid; some integrations may treat any nonzero value as true, while others require exactly `1`.

```sql
CREATE TABLE flags_old (
  id NUMBER PRIMARY KEY,
  active NUMBER(1) CONSTRAINT flags_old_ck CHECK (active IN (0, 1))
);
INSERT INTO flags_old VALUES (1, 1);
SELECT id FROM flags_old WHERE active = 1;
```

## 3. What is different?

```sql
CREATE TABLE flags_new (id NUMBER PRIMARY KEY, active BOOLEAN);
INSERT INTO flags_new VALUES (1, TRUE);
INSERT INTO flags_new VALUES (2, FALSE);
INSERT INTO flags_new VALUES (3, NULL);
SELECT id FROM flags_new WHERE active IS TRUE; -- 1
SELECT id FROM flags_new WHERE active IS UNKNOWN; -- 3
```

**Coach the demonstration:** Ask whether an absent answer means *false*. It does not: `NULL` is still unknown, so `WHERE active IS TRUE` excludes both `FALSE` and `NULL`. Show how the old model requires everyone to remember `1 = true`, while the new one says it in SQL. Also explain that `BOOLEAN` does **not** eliminate business decisions about nullable flags; add `NOT NULL` if the business requires an answer.

**Application boundary:** A JDBC/ORM/reporting stack must support SQL Boolean binding and result retrieval. A legacy API contract returning `'Y'` or `1` will not automatically change because the column type changed.

## 4. What are the advantages and limitations?

| Benefit | Trade-off |
|---|---|
| Clear intent and native Boolean predicates | Check client drivers, ORMs, ETL, and reporting tools |
| No invalid non-Boolean values | Nullable Boolean still has three-valued logic |
| Less conversion logic in new SQL/PLSQL code | Existing interfaces may require explicit conversion |

## 5. When should developers adopt it?

**Adopt** for new true/false attributes when all consuming tools support the type. **Keep** existing `NUMBER(1)` or `CHAR(1)` columns when compatibility costs exceed the readability and correctness gains. Migrate deliberately at API boundaries; do not rewrite stable schemas merely to modernize syntax.

## Key takeaway

**BOOLEAN makes the contract visible in the schema; it does not change the need to define NULL behavior or client compatibility.**

## Documentation — Oracle AI Database 26ai

- [SQL data types, including BOOLEAN and NUMBER/CHAR](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/Data-Types.html)
