# APEX Blueprint

This asset demonstrates a repeatable, AI-assisted workflow for generating Oracle APEX 26.1 applications from structured business requirements and database schema metadata.

The included example generates a Data Product Governance application for managing data products, datasets, access requests, approvals, quality issues, delivery tasks, and audit history.

Reviewed: 26.08.2026

# When to use this asset?
 
Use this asset when you want to:

* Accelerate the creation of a new Oracle APEX application
* Generate an APEX Application Blueprint from business requirements
* Ensure generated pages use approved database tables and columns
* Build reports, forms, dashboards, LOVs, navigation, and access roles
* Demonstrate an AI-assisted APEX development workflow
* Create a starting point that can be reviewed and refined in App Builder

This asset is intended for APEX developers, solution engineers, architects, and teams evaluating AI-assisted application development.
 
# How to use this asset?
 
## Prerequisites

Before starting, ensure that you have:

* Access to an Oracle APEX 26.1 workspace
* Permission to import and create applications
* The required database schema objects
* A local editor such as Visual Studio Code
* An AI assistant capable of processing the supplied specifications and prompts
* Oracle APEX or APEXlang generation guidance available to the AI assistant

SQLcl 26.1.2 or newer and Java 17 or Java 21 are also recommended when using APEXlang validation or command-line import workflows.

## Project Structure

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

## Main Files

* `install.sql`

  * Optional script for creating the supporting database objects.

* `inputs/functional-spec.md`

  * Defines the business objective, users, pages, workflows, security, and user-experience requirements.

* `inputs/schema-metadata.md`

  * Defines the approved tables, columns, primary keys, and foreign keys that the generated application may use.

* `inputs/blueprint-prompt.md`

  * Contains the Oracle APEX 26.1 Blueprint generation instructions.

* `prompts/generating-specs.md`

  * Contains reusable prompts for preparing the functional specification, schema metadata, and blueprint.

* `outputs/generated-blueprint.md`

  * Contains the generated Application Blueprint to import into Oracle APEX.

## Workflow

### 1. Review the functional specification

Open `inputs/functional-spec.md` and confirm that it describes:

* The business objective
* User roles and responsibilities
* Required pages and work areas
* Reports, forms, dashboards, and workflows
* Security expectations
* Application-generation constraints

Use `prompts/generating-specs.md` to generate or refine the specification from a free-form business idea.

### 2. Review the schema metadata

Open `inputs/schema-metadata.md` and confirm that it includes all database objects the application may use.

The metadata should document:

* Tables and columns
* Data types and nullability
* Business descriptions
* Primary keys
* Foreign keys

The generated blueprint should not reference tables or columns that are absent from this file.

### 3. Generate the blueprint

Provide the following files to the AI assistant:

* `inputs/functional-spec.md`
* `inputs/schema-metadata.md`
* `inputs/blueprint-prompt.md`

Save the generated result as:

```text
outputs/generated-blueprint.md
```

The generated blueprint may include:

* Application settings
* Access-control roles
* Lists of values
* Navigation and breadcrumbs
* Dashboards
* Reports and forms
* Master-detail pages
* Related child reports
* Hidden technical keys
* Business-friendly labels

### 4. Import the blueprint

In Oracle APEX:

1. Open App Builder.
2. Select **Import**.
3. Upload `outputs/generated-blueprint.md`.
4. Select **Application Blueprint** as the file type.
5. Complete the import wizard.
6. Create the application from the imported blueprint.

### 5. Correct validation errors

When APEX reports an import or validation error:

1. Copy the complete error message.
2. Provide it to the AI assistant.
3. Ask the assistant to identify the relevant blueprint grammar or validation issue.
4. Update `outputs/generated-blueprint.md`.
5. Update the functional specification or schema metadata when the error originated from unclear source information.
6. Import the corrected blueprint again.

This creates a repeatable feedback loop:

```text
Business requirements
        ↓
Schema metadata
        ↓
Blueprint generation
        ↓
APEX import and validation
        ↓
Correction and refinement
```

### 6. Configure application access

After importing the application:

1. Open the application in App Builder.
2. Go to **Shared Components**.
3. Open **Access Control**.
4. Review the generated roles.
5. Assign the appropriate users.

The example application may include the following roles:

* Business Requester
* Data Product Owner
* Data Steward
* Approver
* Administrator

# Useful Links

* [Oracle APEX](https://apex.oracle.com/)

  * Oracle APEX product information, resources, and workspace access.

* [Oracle APEX Documentation](https://docs.oracle.com/en/database/oracle/apex/)

  * Official Oracle APEX documentation.

* [Oracle APEXlang Skill](https://github.com/oracle/skills/blob/main/apex/apexlang/README.md)

  * Guidance for generating schema-aware and validation-safe Oracle APEX application artifacts.

* [Oracle Skills Repository](https://github.com/oracle/skills)

  * Public repository containing reusable Oracle AI assistant skills.

* [Oracle SQLcl](https://www.oracle.com/database/sqldeveloper/technologies/sqlcl/)

  * Command-line interface for Oracle Database development and automation.

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.
