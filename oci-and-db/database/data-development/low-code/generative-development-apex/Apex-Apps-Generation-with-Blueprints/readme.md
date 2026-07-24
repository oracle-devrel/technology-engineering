# APEX Blueprint

This project demonstrates a practical workflow for generating Oracle APEX applications from Blueprint with an AI assistant. Instead of starting from a blank App Builder canvas, you prepare a business specification, and fetch schema metadata. using the Oracle APEX 26.1 Blueprint prompt, The AI assistant then turns those inputs into an importable APEX Application Blueprint.

With the newer APEX 26.1 blueprint workflow, application generation is much easier to repeat, review, and refine. The assistant can draft pages, dashboards, reports, forms, LOVs, navigation, breadcrumbs, access roles, and detail-page relationships from structured inputs. APEX then imports the blueprint and creates the application scaffold inside the workspace.

The example application in this project is a Data Product Governance app. It helps business users and data teams manage governed data products, dataset catalog records, product requests, access requests, data quality issues, approvals, delivery tasks, and audit history.

## Demo Application

The demo application shows how an organization can manage the lifecycle of data products in one governed workspace. Data Product Governance means making sure important datasets and data products are requested, reviewed, approved, delivered, accessed, monitored, and audited in a controlled way. In simple terms, the app helps teams see what data products exist, who owns them, which datasets they use, who has requested access, what quality issues need attention, what approvals are pending, and what tasks are still open.

## AI-Assisted Application Generation Flow

The process is intentionally simple:

1. Describe the business application you want.
2. Ask the AI assistant to turn that idea into a detailed functional specification.
3. Provide database schema metadata so the assistant knows which tables and columns are allowed.
4. Ask the assistant to generate a complete Oracle APEX 26.1 Blueprint Markdown file.
5. Import the generated blueprint into APEX App Builder.
6. If APEX reports validation errors, give those errors back to the assistant and regenerate or patch the blueprint.

This creates a tight feedback loop: business idea, structured requirements, schema-aware generation, APEX import, validation, and correction. The result is faster than building every page manually, while still keeping the app grounded in real schema metadata.

## AI Assistant Requirements

For best results, the AI assistant should have Oracle APEX and APEXlang generation skills installed or available in its context. These skills help the assistant reason about APEX pages, components, schema metadata, validation behavior, and import-safe output.

The Oracle APEXlang skill can be obtained from the Oracle skills repository:

```text
https://github.com/oracle/skills/blob/main/apex/apexlang/README.md
```

This project uses APEX Blueprint Markdown rather than direct APEXlang app materialization, but the APEXlang skill guidance is still useful because it keeps the assistant disciplined about schema evidence, page generation, validation, and avoiding invented database objects.

## Project Logic

The project follows a controlled generation flow:

1. Capture the business goal in a functional specification.
2. Capture the available database objects in schema metadata.
3. Use the Oracle APEX 26.1 Blueprint System Prompt to generate a complete Application Blueprint.
4. Import the generated blueprint into Oracle APEX.
5. Review any import or validation errors, then update the blueprint or source specifications so the issue does not recur.

The functional specification describes what the app should do. The schema metadata defines what tables and columns the app is allowed to use. The blueprint prompt defines the exact Markdown structure, page patterns, components, validation rules, and APEX 26.1 blueprint grammar.

The generated blueprint should not invent tables or columns. If the application needs a page, report, form, LOV, relationship, or drilldown, it must be built from the schema documented in `inputs/schema-metadata.md`.

## Folder Structure

```text
apex-blueprint-data-product-governance/
  install.sql
  readme.md
  inputs/
    blueprint-prompt.md
    functional-spec.md
    schema-metadata.md
  outputs/
    generated-blueprint.md
    errors.md
  prompts/
    generating-specs.md
```

## Key Files

- `install.sql`: Optional database setup script for the supporting schema objects.
- `inputs/functional-spec.md`: Business requirements, user roles, work areas, UX rules, and generation constraints.
- `inputs/schema-metadata.md`: Authoritative table, column, primary key, and foreign key metadata.
- `inputs/blueprint-prompt.md`: Oracle APEX 26.1 Blueprint System Prompt used to control blueprint generation.
- `prompts/generating-specs.md`: Reusable prompts for generating the functional spec, schema metadata, and blueprint.
- `outputs/generated-blueprint.md`: Final generated Oracle APEX Application Blueprint Markdown.

## Prerequisites

Before using this project, make sure you have:

- Access to an Oracle APEX 26.1 workspace.
- Permission to create or import applications in the target APEX workspace.
- The database schema objects described in `inputs/schema-metadata.md`, or the ability to run `install.sql` if it matches your environment.
- A local editor such as VS Code for reviewing and updating Markdown files.
- An AI assistant or generation workflow capable of following the blueprint prompt and writing `outputs/generated-blueprint.md`.
- Oracle APEXlang skills available to the AI assistant. See the Oracle APEXlang skill README at `https://github.com/oracle/skills/blob/main/apex/apexlang/README.md`.
- SQLcl 26.1.2 or newer and Java 17 or Java 21 if you plan to use live APEXlang validation or import workflows outside the manual APEX Blueprint import path.


## Workflow

### 1. Prepare Or Review The Functional Specification

Open `inputs/functional-spec.md` and confirm that it describes the intended application in business terms.

The functional spec should include:

- Business objective
- User types and responsibilities
- Main work areas
- Required pages and workflows
- Report, form, dashboard, and detail-page expectations
- Security expectations
- UX and blueprint generation constraints

Use `prompts/generating-specs.md` if you want the assistant to generate or refine the functional specification from a free-form idea.

### 2. Prepare Or Review The Schema Metadata

Open `inputs/schema-metadata.md` and confirm that it includes every table and column the blueprint is allowed to use.

The schema metadata should include:

- Table names
- Column names
- Data types
- Nullability
- Business descriptions
- Primary keys
- Foreign keys

Do not rely on prose requirements to invent schema structure. If a table or column is not in the schema metadata, it should not appear in the generated blueprint.

### 3. Generate The Blueprint

Ask the assistant to use:

- `inputs/functional-spec.md`
- `inputs/schema-metadata.md`
- `inputs/blueprint-prompt.md`

The output should be saved as:

```text
outputs/generated-blueprint.md
```

The blueprint should include:

- Application definition
- Access controls and roles
- LOVs
- Page groups
- Navigation menu
- Breadcrumbs
- Dashboard pages
- Reports
- Forms
- Detail pages with related child reports
- Hidden technical primary keys
- Business-friendly labels

### 4. Import The Blueprint Into Oracle APEX

In the target APEX workspace:

1. Go to App Builder.
2. Select Import.
3. Upload `outputs/generated-blueprint.md`.
4. Choose the file type `Application Blueprint`.
5. Continue through the import wizard.
6. Create the application from the imported blueprint.

### 5. Handle Import Or Validation Errors

If APEX reports errors:

1. Copy the full error output and paste it directly into your AI assistant.
2. Ask the assistant to inspect the error output and identify the exact blueprint rule or grammar issue.
3. Patch `outputs/generated-blueprint.md` based on the reported errors.
4. If the issue came from unclear source requirements, update `inputs/functional-spec.md` or `inputs/schema-metadata.md` so the next generation avoids the same error.
5. Re-import the corrected blueprint.



### 6. Configure Access After Import

After a successful import:

1. Open the generated application in App Builder.
2. Go to Shared Components.
3. Open Access Control.
4. Review the generated roles.
5. Create or assign users to the appropriate roles.

Expected roles for this application include:

- Business Requester
- Data Product Owner
- Data Steward
- Approver
- Administrator
