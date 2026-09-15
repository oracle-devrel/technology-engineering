# Data Product Governance Functional Specification

## Objective

Build an Oracle APEX application for managing data product requests, dataset catalog records, access requests, data quality issues, approvals, delivery tasks, and audit history.

The application should help business users and data teams track the lifecycle of governed data products from request intake through review, delivery, publication, and ongoing support.

## Users

The application supports these user types:

- Business Requester: submits data product requests, access requests, and data quality issues.
- Data Product Owner: reviews product requests, tracks delivery, and owns product status.
- Data Steward: manages dataset metadata, reviews access requests, and resolves quality issues.
- Approver: approves or rejects submitted requests.
- Administrator: manages reference data and monitors all activity.

## Main Work Areas

The application should include these areas:

- Home
- Data Products
- Datasets
- Requests
- Data Quality
- Approvals
- Tasks
- Audit

## Home

The Home page should provide a simple operational dashboard.

It should show:

- Total data products
- Open product requests
- Pending access requests
- Open data quality issues
- Pending approvals
- Open tasks

It should also include quick access to:

- Submit a product request
- Submit an access request
- Report a data quality issue
- Review pending approvals

## Data Products

Users should be able to view and manage data products.

A data product includes:

- Product name
- Business domain
- Business owner
- Status
- Priority
- Requested by
- Requested on
- Target delivery date
- Description

The Data Products area should include:

- A searchable list of data products
- A detail page for a selected data product
- Related product requests
- Related datasets
- Related tasks
- Related audit events

Users should be able to create and edit data products.

## Datasets

Users should be able to view and manage governed datasets.

A dataset includes:

- Dataset name
- Source system
- Business domain
- Classification
- Steward name
- Refresh frequency
- Status
- Description

The Datasets area should include:

- A searchable dataset catalog
- A detail page for a selected dataset
- Related data products
- Related access requests
- Related data quality issues

Users should be able to create and edit datasets.

## Product Requests

Users should be able to submit and track requests for new data products, enhancements, changes, or retirement.

A product request includes:

- Request title
- Related data product
- Requester name
- Business unit
- Request type
- Status
- Priority
- Submitted on
- Due date
- Justification

The Product Requests area should include:

- A list of product requests
- A detail page for each request
- Approval history
- Related tasks
- Related audit events

Users should be able to create and edit product requests.

## Access Requests

Users should be able to request access to governed datasets.

An access request includes:

- Dataset
- Requester name
- Access purpose
- Access level
- Status
- Requested on
- Approved by
- Decision date

The Access Requests area should include:

- A list of access requests
- A detail page for each access request
- Approval history
- Related audit events

Users should be able to create and edit access requests.

## Data Quality Issues

Users should be able to report and track data quality issues.

A data quality issue includes:

- Dataset
- Issue title
- Severity
- Status
- Reported by
- Reported on
- Assigned to
- Resolution notes

The Data Quality area should include:

- A list of quality issues
- A detail page for each issue
- Related tasks
- Related audit events

Users should be able to create and edit quality issues.

## Approvals

Users should be able to review pending approvals.

An approval includes:

- Request type
- Request ID
- Approver name
- Decision
- Decision date
- Comments

The Approvals area should include:

- A pending approvals queue
- A full approval history report
- Approval detail and edit capability

Users should be able to update approval decisions.

## Tasks

Users should be able to track work required to deliver requests or resolve issues.

A task includes:

- Related type
- Related ID
- Task name
- Assigned to
- Status
- Due date

The Tasks area should include:

- A list of open tasks
- A detail page for each task
- Task edit capability

## Audit

Users should be able to review important events across the application.

An audit event includes:

- Event type
- Entity name
- Entity ID
- Event by
- Event on
- Event note

The Audit area should include:

- A searchable audit event report
- Filters by entity name, event type, user, and event date

Audit events are read-only.

## Navigation

The application should use clear navigation entries for:

- Home
- Data Products
- Datasets
- Product Requests
- Access Requests
- Data Quality Issues
- Approvals
- Tasks
- Audit Events

## User Experience Rules

The application should be simple, business-friendly, and easy to navigate.

Use business-facing labels instead of technical table names.

Primary key values should remain hidden from end users.

Users should navigate from lists to detail pages without re-entering the selected record.

Related information should appear on detail pages where it helps users complete work.

Reports should support filtering, sorting, searching, and exporting where appropriate.

Forms should be used for creating and editing records.

## Blueprint Generation Constraints

When generating Oracle APEX Blueprint Markdown, use only valid APEX 26.1 render role values for each component type.

For Interactive Report and Classic Report columns:

- Include an explicit Render As value on every report column.
- Use Render As: hidden for technical primary key and foreign key values that should not be shown to end users.
- Use Render As: plainText for normal display-only business columns.
- Use Render As: plainTextBasedOnLov only when the column references a defined LOV.

For Content Row regions used on detail pages:

- Use Render As: title2 for the primary display value.
- Use Render As: overline for one secondary context value.
- Use Render As: description for one long descriptive value.
- Use Render As: miscellaneous for at most one additional supporting value.
- Use Render As: hidden for technical identifiers and any extra supporting columns that do not fit the allowed Content Row roles.
- Do not use Render As: title, subtitle, or misc.
- Do not repeat the same visible Content Row role more than once in a single Content Row region.

Preferred Content Row mappings for detail pages:

- Data Product Detail: Product name as title2, business domain as overline, description as description, and one supporting value as miscellaneous; hide remaining supporting values.
- Dataset Detail: Dataset name as title2, source system as overline, description as description, and one supporting value as miscellaneous; hide remaining supporting values.
- Product Request Detail: Request title as title2, related data product as overline, justification as description, and one supporting value as miscellaneous; hide remaining supporting values.
- Access Request Detail: Requester name as title2, dataset name as overline, access purpose as description, and one supporting value as miscellaneous; hide remaining supporting values.
- Quality Issue Detail: Issue title as title2, dataset name as overline, resolution notes as description, and one supporting value as miscellaneous; hide remaining supporting values.
- Task Detail: Task name as title2, related type as overline, and one supporting value as miscellaneous; hide remaining supporting values.

## Security Expectations

Business Requesters should submit and view their own requests.

Data Product Owners should manage data products and related delivery tasks.

Data Stewards should manage datasets, access requests, and quality issues.

Approvers should review and update approval decisions.

Administrators should have full access.

## Out of Scope

The generated application does not need to include:

- External system integrations
- Email notifications
- Advanced workflow automation
- Custom PL/SQL approval logic
- Fine-grained row-level security
- Production-ready authorization rules

These can be added after the application scaffold is generated.
