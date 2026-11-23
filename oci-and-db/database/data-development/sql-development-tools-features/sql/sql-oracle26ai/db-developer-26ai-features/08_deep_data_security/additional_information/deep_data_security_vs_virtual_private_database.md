# Oracle Deep Data Security vs. Virtual Private Database

> **Developer question:** We already filter rows with Virtual Private Database. Why should we consider Oracle Deep Data Security?

## 1. What is the new capability?

**Oracle Deep Data Security** introduces declarative data grants and an end-user/data-role authorization model enforced by the database. It can govern row and column access, including what an application end user may see through shared database connections. **Virtual Private Database (VPD)** remains a mature policy-based mechanism that dynamically adds predicates to SQL statements.

## 2. How did we solve this before?

VPD uses a PL/SQL policy function to return a SQL predicate, attached to a protected table or view through `DBMS_RLS`. The application typically sets a trusted context identifying the user or tenant.

```sql
-- Assumes DEMO_ORDERS(owner_id, amount) and a secure APP_CTX context.
CREATE OR REPLACE FUNCTION orders_vpd_predicate(
  p_schema VARCHAR2, p_object VARCHAR2
) RETURN VARCHAR2 AS
BEGIN
  RETURN 'owner_id = SYS_CONTEXT(''APP_CTX'', ''USER_ID'')';
END;
/
BEGIN
  DBMS_RLS.ADD_POLICY(
    object_schema => USER,
    object_name => 'DEMO_ORDERS',
    policy_name => 'ORDERS_BY_OWNER',
    function_schema => USER,
    policy_function => 'ORDERS_VPD_PREDICATE');
END;
/
```

## 3. What is different?

Deep Data Security expresses authorization using data grants to **Deep Data Security end users or data roles**, not ordinary database roles. The example below illustrates the grant shape; it requires a configured Deep Data Security end user/data role and proper privileges.

```sql
-- DEMO_READER must be a Deep Data Security end user or data role.
CREATE DATA GRANT own_orders AS SELECT
  ON demo_orders
  WHERE owner_id = SYS_CONTEXT('APP_CTX', 'USER_ID')
  TO demo_reader;
```

**Coaching walkthrough:** Alice and Bob use the same application connection pool. Alice should see only Alice's orders; Bob should see only Bob's. In VPD, the policy function supplies a predicate based on a securely established session context. In Deep Data Security, a declarative data grant also describes *who* has access, with a model for propagating and enforcing end-user identity. Both depend on **trusted identity propagation**; a forged or stale context is a security failure, not a feature comparison win.

**Runtime enforcement:** VPD rewrites applicable SQL with the policy predicate. Deep Data Security evaluates applicable grants and their row/column predicates for the current end-user authorization context. Column restrictions can result in inaccessible cells appearing as `NULL` under documented semantics. **Critical deployment nuance:** simply creating a data grant does not mean every database-user access path is automatically denied; mandatory data-grant-only enforcement and the application's end-user context must be configured and tested. Validate bypass routes, definer-rights code, administrative privileges and connection-pool context reset.

## 4. What are the advantages and limitations?

| Deep Data Security | Virtual Private Database |
|---|---|
| Declarative row/column grants for application end users/data roles | Flexible policy functions and SQL predicates |
| Designed for database-enforced end-user authorization | Mature deployments and established operational patterns |
| Requires identity, grants and enforcement configuration | Requires secure application contexts and PL/SQL policy maintenance |
| Migration needs policy-equivalence and bypass testing | Existing policies may already satisfy the business requirement |

## 5. When should developers adopt it?

**Consider Deep Data Security** for new applications needing database-enforced, fine-grained authorization tied to application end users, especially with pooled connections. **Keep VPD** where it is correct, well tested and maintainable; do not migrate on naming alone. Build tests for Alice/Bob access, denied columns, direct SQL access, privileged bypasses and pooled-session identity leakage before switching.

## Key takeaway

**VPD controls data through dynamically supplied SQL predicates; Deep Data Security adds a declarative end-user authorization model. Both require correct identity handling.**

## Documentation — Oracle AI Database 26ai

- [CREATE DATA GRANT](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-data-grant.html)
- [Using Oracle Virtual Private Database to Control Data Access](https://docs.oracle.com/en/database/oracle/oracle-database/26/dbseg/using-oracle-vpd-to-control-data-access.html)
