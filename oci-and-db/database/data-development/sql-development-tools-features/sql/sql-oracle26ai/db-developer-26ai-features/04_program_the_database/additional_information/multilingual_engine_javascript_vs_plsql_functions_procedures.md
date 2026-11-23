# Multilingual Engine (MLE) JavaScript vs. PL/SQL Functions and Procedures

> **Developer question:** Why run JavaScript *inside Oracle Database* when PL/SQL already supports functions and procedures — or when our application server already runs JavaScript?

## 1. What is the new capability?

**Multilingual Engine (MLE) for JavaScript** lets developers store and execute server-side JavaScript in the database. JavaScript can be defined as an MLE module and exposed to SQL or PL/SQL through a familiar function/procedure **call specification**. This does **not** replace SQL or PL/SQL: it adds another language for database-resident logic.

**Audience angle:** It is especially relevant to full-stack JavaScript/TypeScript teams, teams with reusable *compatible* JavaScript business logic, and database developers integrating code that is clearer or easier to maintain in JavaScript. An APEX or PL/SQL team with mature PL/SQL packages may have no reason to migrate existing code.

## 2. How did we solve this before?

Traditionally, put data-intensive logic in PL/SQL, or run JavaScript on an application server that calls the database over a network. For a simple reusable function:

```sql
CREATE OR REPLACE FUNCTION normalize_code_plsql(p_code VARCHAR2)
RETURN VARCHAR2 IS
BEGIN
    RETURN UPPER(TRIM(p_code));
END;
/
SELECT normalize_code_plsql('  ab-12  ') FROM dual; -- AB-12
```

PL/SQL already has excellent SQL integration, transaction handling, package APIs, and a mature database-specific ecosystem. For this trivial example, **there is no compelling reason to use MLE**.

## 3. What is different?

The same operation can be written in JavaScript and exposed as a SQL-callable function:

```sql
-- Requires appropriate MLE and CREATE PROCEDURE privileges.
CREATE OR REPLACE MLE MODULE code_utils_js
LANGUAGE JAVASCRIPT AS
export function normalizeCode(code) {
    return code.trim().toUpperCase();
}
/

CREATE OR REPLACE FUNCTION normalize_code_js(p_code VARCHAR2)
RETURN VARCHAR2
AS MLE MODULE code_utils_js
SIGNATURE 'normalizeCode(string)';
/

SELECT normalize_code_js('  ab-12  ') FROM dual; -- AB-12
```

**Coaching walkthrough:** The JavaScript function is exported from a **database schema object**; the SQL call specification provides a familiar database API; callers need not know whether the implementation is JavaScript or PL/SQL. Contrast this with JavaScript running in Node.js: MLE code executes **in the database process**, near the data, rather than on a separate application server. That can avoid application-to-database network round trips for suitable workloads, but it also consumes database resources.

**Where the value becomes more interesting:** imagine a team already maintains a sophisticated JavaScript validation or transformation library (for example, parsing structured input or applying complex domain-specific text rules). If its dependencies and runtime APIs are compatible with MLE, the team may be able to reuse the algorithm in-database rather than rewrite it in PL/SQL or shuttle many values back to an application tier. The example above proves the *integration model*, not a performance advantage.

## 4. What are the advantages and limitations?

| Potential benefit | Important qualification |
|---|---|
| Familiar JavaScript syntax and shared skills for full-stack teams. | PL/SQL remains more natural for many database-centric operations. |
| Reuse of JavaScript modules and selected third-party packages. | **Not every npm package works.** MLE uses ECMAScript modules; packages depending on Node.js built-ins, native add-ons, filesystem access, or unsupported APIs may need adaptation or be unusable. |
| Run compatible transformations near data, callable from SQL/PLSQL. | Database CPU/memory are valuable; benchmark against SQL, PL/SQL, and the application tier. |
| JavaScript modules can call SQL via MLE's SQL driver. | SQL remains the preferred tool for set-based data manipulation; avoid replacing efficient SQL with row-by-row JavaScript. |
| Database security and grants govern deployment and execution. | Review third-party code and grant minimal privileges: it executes with database-access capabilities. |

**Library reality check:** MLE supports module imports and built-in JavaScript modules, but it is **not a general Node.js server** and does not offer arbitrary Node filesystem/network APIs. Modules are deployed as database objects, with MLE environments handling import resolution when needed. External integrations and package compatibility must be evaluated individually.

## 5. When should developers adopt it?

**Consider MLE when** the development team has JavaScript expertise, a reusable compatible library, or a well-bounded transformation that benefits from execution close to the data. Start with a small, independently testable function and measure resource use and deployment complexity. **Keep PL/SQL when** the code is primarily SQL orchestration, transaction logic, database APIs, or already works well; keep application-server JavaScript when it needs the Node ecosystem, filesystem/network integrations, independent scaling, or external service coordination.

**Live coaching prompt:** “If a JS team has a validated parser used by its app, should we rewrite it in PL/SQL just to run it near the data?” Not necessarily — evaluate MLE compatibility first. “Should we move the entire Node backend into the database?” No — MLE is a targeted in-database execution option, not a wholesale application-server replacement.

## Key takeaway

**MLE changes who can write database-resident logic and which JavaScript code can be reused; it does not make JavaScript inherently better than PL/SQL.** Its strongest adoption case is compatible JavaScript expertise/code plus a real reason to execute near the data.

## Documentation — Oracle AI Database 26ai

- [MLE JavaScript modules and call specifications — JavaScript Developer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/26/mlejs/creating-call-specification-mle-module.html)
- [CREATE FUNCTION — SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/CREATE-FUNCTION.html)
