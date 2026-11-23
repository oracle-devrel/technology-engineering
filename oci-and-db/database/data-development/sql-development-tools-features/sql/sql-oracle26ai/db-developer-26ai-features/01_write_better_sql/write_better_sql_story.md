# Write Better SQL

## Presenter purpose
Show experienced SQL developers that the value of newer syntax is not novelty: it is removing query scaffolding while preserving the business answer. This is an invitation to simplify SQL they already maintain, not to rewrite every query.

## Introduction — why developers should care
A report asks for the most recent order per customer, several conditional totals, and a breakdown by region. Traditionally, even a simple business question can require an outer SELECT for analytic filtering, CASE expressions inside aggregates, and repeated grouping expressions. Each extra copy is another place to make a mistake when requirements change.

The audience should recognize these patterns immediately. Emphasize **clarity and maintainability**, not an unproven speedup: a shorter query is not automatically a faster query.

## The capabilities and what to notice

### QUALIFY — filter the analytic result where it is calculated
Ranking and latest-row logic commonly uses `ROW_NUMBER()` in an inner query and filters `rn = 1` outside. `QUALIFY` expresses the analytic filter in the same query block. A developer reading the statement sees the ranking rule and the filter together. Useful for top-N, deduplication, and latest-record reporting.

### FILTER — put a condition on an aggregate
Instead of repeating `SUM(CASE WHEN status = 'PAID' THEN amount END)` for each conditional measure, the aggregate can carry its own `FILTER (WHERE ...)` clause. This makes a dashboard's paid/open/canceled measures easier to extend without burying the condition inside the expression.

### GROUP BY improvements — name business dimensions once
`GROUP BY ALL` derives grouping expressions from the non-aggregate select list. Select-list aliases can also make derived grouping dimensions easier to reuse in supported grouping clauses. Positional grouping is possible when the relevant session setting is enabled, but aliases are generally clearer in maintained code. The notebook also illustrates reporting extensions such as ROLLUP, CUBE, and GROUPING SETS.

## Demo coaching
Use `write_better_sql_demo.sqlnb`. Compare traditional and newer statements **side by side**. Ask the audience what code disappeared, then check that the returned rows still express the same business answer. For QUALIFY, point to the missing wrapper query; for FILTER, point to the condition beside the aggregate; for GROUP BY, point to the eliminated duplicate business expression.

Avoid claiming performance improvements without plans or measurements. The demonstrable benefit is simpler SQL structure.

## Close-out — the memorable point
The SQL now looks more like the question we are trying to answer. Less nesting and less repetition mean fewer moving parts to review when a reporting requirement changes. Developers can try these features first in queries that are already difficult to read, rather than changing well-understood SQL merely for style.

## Presenter follow-up
If asked whether the optimizer will always generate the same plan, say the demonstration establishes equivalent results and clearer expression, not universal plan equivalence. Compare execution plans on real workloads when performance matters.

**Assets:** `write_better_sql_demo.sqlnb`, `write_better_sql_cleanup.sql`.
