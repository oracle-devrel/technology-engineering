# Program the Database

## Presenter purpose
Introduce MLE JavaScript as an **additional database-resident programming choice**, not a replacement for PL/SQL or an invitation to move arbitrary server code into the database.

## Introduction — why developers should care
Database developers already know why PL/SQL is useful near the data. But application teams may have JavaScript skills, transformations, or existing libraries they want to reuse. Multilingual Engine (MLE) lets suitable JavaScript run inside Oracle Database, reducing the need for a separate service merely to execute that logic near database data.

## How it works
A persistent **MLE module** stores JavaScript as a schema object. A **call specification** exposes a function through a SQL/PLSQL interface. Callers can use the published function without needing to know its implementation language. This is a bridge between JavaScript-oriented developers and established database interfaces.

MLE supports JavaScript modules and a useful subset of the JavaScript ecosystem, but not every Node.js package will run unchanged. Libraries with unsupported native bindings, OS access, or runtime assumptions need evaluation. Database privileges, execution limits, security, and resource consumption still matter. A language option is not automatically a performance advantage over PL/SQL.

## Demo coaching
Use `program_the_database_demo.sqlnb`: check relevant MLE settings and privileges, create a JavaScript module for email normalization/validation, publish a call specification, and invoke it from SQL. Point out **where the code lives** and **how the SQL caller sees it**, not JavaScript syntax.

The email example is deliberately small. For a simple reusable email constraint, a **Domain** is often more appropriate. MLE becomes interesting for procedural transformation, JavaScript-oriented teams, or carefully selected reusable JS logic.

## Where this could matter
A service team already maintains JavaScript parsing or transformation logic and wants that behavior available within database-side workflows. The database team can expose a stable SQL/PLSQL signature while implementation details remain in the module. That can reduce unnecessary data movement and application tiers in the right architecture, but deployment and package governance need ownership.

## Close-out — the memorable point
PL/SQL remains central. MLE adds another language for work that genuinely belongs close to Oracle data. The decision is driven by team skills, reusable logic, security, and operational fit—not by JavaScript being newer.

## Presenter follow-up
If asked **why not PL/SQL?**, acknowledge that PL/SQL is usually the simpler default for SQL-heavy database logic. If asked **why not run JS in the app tier?**, explain the trade-off between reducing round trips and adding runtime responsibility to the database. Avoid promising universal compatibility with the npm ecosystem.

**Assets:** `program_the_database_demo.sqlnb`, `program_the_database_cleanup.sql`.
