# Generating Functional Spec form Idea
You are helping me create a reusable Oracle APEX 26.1 blueprint demo.

Application idea:
Data Product Governance application for managing data product requests, dataset catalog records, access requests, data quality issues, approvals, tasks, and audit history.

Generate a clear functional specification in Markdown.

Keep it business-readable and structured.

Include:
- Objective
- User roles
- Main work areas
- Key workflows
- Pages the application should include
- User experience expectations
- Security expectations
- Out-of-scope items

Do not include technical implementation details unless needed.

# Generating Metadata Spec from schema

Use the attached `install.sql` file.

Generate a `schema-metadata.md` file that describes the schema for an Oracle APEX 26.1 blueprint generation process.

For each table, include:
- Table name
- Business description
- Columns
- Data types
- Nullable status
- Primary key
- Foreign keys
- Important comments or business meaning

Return the result in clean Markdown.
Do not invent tables or columns.

# Generating the Blueprint
You are an Oracle APEX 26.1 application generation agent.

Use these inputs:
- `functional-spec.md`
- `schema-metadata.md`
- Oracle APEX 26.1 Blueprint System Prompt `blueprint-prompt.md`

Generate a complete Oracle APEX 26.1 Application Blueprint in Markdown.

The blueprint should:
- Follow the functional specification
- Use only the provided schema
- Create appropriate pages, reports, forms, dashboards, navigation, LOVs, and relationships
- Use business-friendly labels
- Hide technical primary key values from end users
- Include detail pages with related child reports where useful
- Prefer standard APEX components
- Avoid inventing tables or columns

Return only the final importable blueprint Markdown.

Save the output as `generated-blueprint.md`.