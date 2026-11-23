# Developer Productivity

## Presenter purpose
Make the audience recognize familiar development friction and show how Oracle reduces repetitive setup, metadata, and delivery work. Finish by connecting the **SQL Developer extension in VS Code**, SQL Notebooks, and SQLcl to the tools used throughout the session.

## Introduction — why developers should care
Most developers have rerun a setup script and seen `object already exists`. Sometimes that error is valuable; sometimes it is just noise when a script is intended to be repeatable. Teams also reconstruct metadata from dictionary views and keep schema-aware tools synchronized after DDL changes. These tasks are small individually but expensive when repeated across projects.

## The capabilities and what to notice

### IF EXISTS / IF NOT EXISTS — express repeatability in DDL
Instead of wrapping every DDL operation in dictionary checks or exception handlers, supported statements can express the intended existence behavior. The important caution: **IF NOT EXISTS is not a schema migration system**. It does not prove an existing object has the desired definition. Use it for suitable repeatable setup, not to conceal drift in production deployments.

### DBMS_DEVELOPER — structured object metadata
Database tooling often needs a consistent description of a table or other supported object. `DBMS_DEVELOPER.GET_METADATA` returns structured metadata that tools can consume without rebuilding the same dictionary query logic. Think IDEs, schema-aware applications, or App Memory Grid-style systems maintaining a picture of database objects.

### Table DDL Change Notification — respond instead of polling
An OCI client registered for supported table DDL notifications can learn that a definition changed. It can then call `DBMS_DEVELOPER` to fetch the **current** definition and refresh a cache. The notification is the signal; the metadata API supplies the description. This is especially useful for middleware and developer tooling, and requires appropriate client and database configuration.

### SQL Developer for VS Code and SQLcl — connected delivery
The demonstrations in this presentation use the SQL Developer extension in VS Code and SQL Notebooks. This keeps familiar SQL/PLSQL work in a workspace that can participate in Git review and application development. SQLcl provides scripting and project-oriented deployment capabilities. The value is a more traceable **edit → review → test → deploy** flow, not a claim that an IDE alone creates collaboration.

## Demo coaching
In `developer_productivity_demo.sqlnb`, compare the old existence-check pattern with `CREATE TABLE IF NOT EXISTS`, then inspect structured metadata through `DBMS_DEVELOPER`. The notification slide illustrates how a registered OCI client can use that metadata after a DDL event; the SQL notebook does not implement an OCI callback.

After the demo, draw attention to the tool already on screen: *"If you have not noticed, I have been running these examples as SQL Notebooks in the SQL Developer extension for VS Code."* Then connect SQLcl and Git-based review to repeatable delivery.

## Close-out — the memorable point
Less defensive DDL, better metadata access, and schema-change signals reduce the work around database development. Combined with familiar tools and a modern delivery workflow, these improvements make database code easier to maintain alongside application code.

**Assets:** `developer_productivity_demo.sqlnb`, `developer_productivity_cleanup.sql`.
