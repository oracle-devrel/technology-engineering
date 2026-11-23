# Data Use Case Domains vs. Table CHECK Constraints

> **Developer question:** If a `CHECK` constraint already enforces a rule, why introduce a Domain?

## 1. What is the new capability?

A **Data Use Case Domain** is a reusable schema-level definition of a business value: an underlying SQL type plus optional validation, display, ordering, and annotations. Associating columns with the same domain applies its reusable semantics while the columns remain ordinary scalar SQL values.

## 2. How did we solve this before?

Developers duplicated checks on each table. A `CHECK` works well locally, but repeated rules can drift when one table is changed and another is forgotten.

```sql
CREATE TABLE discount_old (
  id NUMBER PRIMARY KEY,
  pct NUMBER CHECK (pct BETWEEN 0 AND 100)
);
CREATE TABLE campaign_old (
  id NUMBER PRIMARY KEY,
  pct NUMBER CHECK (pct BETWEEN 0 AND 100)
);
```

## 3. What is different?

```sql
CREATE DOMAIN percent_domain AS NUMBER
  CONSTRAINT percent_range CHECK (percent_domain BETWEEN 0 AND 100);

CREATE TABLE discount_new (id NUMBER PRIMARY KEY, pct percent_domain);
CREATE TABLE campaign_new (id NUMBER PRIMARY KEY, pct percent_domain);

INSERT INTO discount_new VALUES (1, 15);   -- accepted
INSERT INTO campaign_new VALUES (1, 150);  -- rejected by domain constraint
```

**Coaching sequence:** Show the same invalid value failing in either table. Ask the room to find every place the 0–100 rule lives in the old design. Then point to the single domain definition in the new design. A domain is **not** a magic global rule-update switch: changing core constraints on a deployed domain may require replacement and reassociation, so dependencies still matter.

**Where a domain is not the answer:** `CHECK (start_date <= end_date)` is a table-row relationship between columns, not a reusable rule for one scalar value. Keep that as a table constraint. Multicolumn domains exist, but they should be chosen intentionally for reusable cross-column concepts.

## 4. What are the advantages and limitations?

| Domain | Table CHECK |
|---|---|
| Reusable business concept across tables | Self-contained rule for one table |
| Optional presentation/annotation metadata | Simple, mature local constraint |
| Central definition reduces accidental drift | Easy to evolve independently |
| Dependency management when changing the domain | Duplicated rules need coordinated maintenance |

## 5. When should developers adopt it?

**Use domains** for repeatedly modeled concepts such as percentages, postal codes, and standardized identifiers. **Use table CHECK constraints** for local invariants, cross-column relationships, or one-off rules. They complement each other and can coexist.

## Key takeaway

**CHECK is where a rule is enforced; a Domain is how a reusable business meaning and its rules are defined once and associated with many columns.**

## Documentation — Oracle AI Database 26ai

- [CREATE DOMAIN](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-domain.html)
- [Constraint clauses](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/constraint.html)
