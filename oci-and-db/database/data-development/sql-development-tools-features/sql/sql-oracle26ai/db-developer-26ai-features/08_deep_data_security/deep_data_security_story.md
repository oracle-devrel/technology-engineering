# Deep Data Security

## Presenter purpose
Finish the technical story with a consistent authorization boundary. As SQL, JSON, reporting, integrations, and AI-generated queries all reach business data, end-user permissions must not depend on every access path remembering its own filter.

## Introduction — why developers should care
A service account may be able to query many employee records, but an individual user should only see permitted rows and update permitted fields. If every API, report, and integration implements that rule independently, a new access path can accidentally bypass it. AI-generated SQL makes that concern more visible, but it is fundamentally a long-standing application authorization problem.

## The capabilities and what to notice

### Data roles and data grants — a shared policy
Deep Data Security defines fine-grained permissions through data roles and grants. Policies can describe permitted operations, rows, and columns. The goal is to make authorization a property enforced at the data boundary rather than scattered across controllers, UI screens, and ad hoc SQL.

### Trusted end-user context — distinguish people behind a service
The database needs a trustworthy identity context to apply a person's policy when requests arrive through an application service. A database schema owner or pooled service account is not automatically the same as the end user. Proper identity propagation and configuration are essential; simply creating a grant does not prove end-user enforcement.

### Column-scoped updates — permission is more than row filtering
An employee might update their own phone number but not salary. A policy can combine a row condition with a narrower set of permitted update columns. This is useful when multiple applications share employee data and should honor the same boundary.

## Demo coaching
`deep_data_security_demo.sqlnb` creates sample employee data, a data role, and data grants for row-scoped reads and column-scoped updates. It inspects policy definitions. Explain that an end-to-end test would run the **same SQL** under distinct authenticated end-user contexts and compare the authorized results; that requires a configured security environment.

Do not describe this as just filtering by email in application SQL, and do not imply that a policy definition alone demonstrates production identity integration.

## Where this could matter
Think of employee self-service, multi-tenant applications, shared reporting, and AI assistants that generate SQL. Database-enforced permissions help reduce authorization drift as new access paths are introduced. The security team still owns identity trust, privileges, and operational policy design alongside the application team.

## Close-out — the memorable point
More flexible data access is useful only when access remains trustworthy. Deep Data Security offers a shared authorization boundary for rows, columns, and operations, helping developers add new application and AI access paths without duplicating every end-user rule.

**Assets:** `deep_data_security_demo.sqlnb`, `deep_data_security_cleanup.sql`.
