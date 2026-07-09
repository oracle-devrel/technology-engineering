# Provenance
- Source Prompt: blueprint-prompt.md (v26.1.220)
- Functional Requirements: functional-spec.md
- Schema Metadata: schema-metadata.md
- UX Patterns: Built-in
# Application Definition
- Name: Data Product Governance
- Description: Application for governed data product request intake, dataset catalog management, access requests, data quality issues, approvals, delivery tasks, and audit review.
- Comments: Uses DPG_DATA_PRODUCTS, DPG_DATASETS, DPG_PRODUCT_REQUESTS, DPG_PRODUCT_DATASETS, DPG_ACCESS_REQUESTS, DPG_QUALITY_ISSUES, DPG_APPROVALS, DPG_TASKS, and DPG_AUDIT_EVENTS only.
- Primary Application Language: en
- Home Page: Page 1
- Access Controls:
  - Roles:
    - Role: Business Requester
      - Description: Submits and tracks product requests, access requests, and quality issues.
    - Role: Data Product Owner
      - Description: Manages data products, product requests, and delivery tasks.
    - Role: Data Steward
      - Description: Manages datasets, access requests, and quality issues.
    - Role: Approver
      - Description: Reviews and updates approval decisions.
    - Role: Administrator
      - Description: Manages reference activity and monitors all records.
- List of Values:
  - LOV
    - Name: LOV_PRODUCTS
    - Type: Table
    - Table Name: DPG_DATA_PRODUCTS
    - Display: PRODUCT_NAME
    - Return: PRODUCT_ID
  - LOV
    - Name: LOV_DATASETS
    - Type: Table
    - Table Name: DPG_DATASETS
    - Display: DATASET_NAME
    - Return: DATASET_ID
  - LOV
    - Name: LOV_PRODUCT_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Draft
        - Return: Draft
      - Entry:
        - Display: Under Review
        - Return: Under Review
      - Entry:
        - Display: Approved
        - Return: Approved
      - Entry:
        - Display: In Development
        - Return: In Development
      - Entry:
        - Display: Published
        - Return: Published
      - Entry:
        - Display: Retired
        - Return: Retired
  - LOV
    - Name: LOV_PRIORITY
    - Type: Static
    - Entries:
      - Entry:
        - Display: Low
        - Return: Low
      - Entry:
        - Display: Medium
        - Return: Medium
      - Entry:
        - Display: High
        - Return: High
      - Entry:
        - Display: Critical
        - Return: Critical
  - LOV
    - Name: LOV_DATASET_CLASSIFICATION
    - Type: Static
    - Entries:
      - Entry:
        - Display: Public
        - Return: Public
      - Entry:
        - Display: Internal
        - Return: Internal
      - Entry:
        - Display: Confidential
        - Return: Confidential
      - Entry:
        - Display: Restricted
        - Return: Restricted
  - LOV
    - Name: LOV_DATASET_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Draft
        - Return: Draft
      - Entry:
        - Display: Active
        - Return: Active
      - Entry:
        - Display: Deprecated
        - Return: Deprecated
      - Entry:
        - Display: Retired
        - Return: Retired
  - LOV
    - Name: LOV_REQUEST_TYPE
    - Type: Static
    - Entries:
      - Entry:
        - Display: New Product
        - Return: New Product
      - Entry:
        - Display: Enhancement
        - Return: Enhancement
      - Entry:
        - Display: Change
        - Return: Change
      - Entry:
        - Display: Retirement
        - Return: Retirement
  - LOV
    - Name: LOV_REQUEST_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Submitted
        - Return: Submitted
      - Entry:
        - Display: Under Review
        - Return: Under Review
      - Entry:
        - Display: Approved
        - Return: Approved
      - Entry:
        - Display: Rejected
        - Return: Rejected
      - Entry:
        - Display: Completed
        - Return: Completed
  - LOV
    - Name: LOV_ACCESS_LEVEL
    - Type: Static
    - Entries:
      - Entry:
        - Display: Read
        - Return: Read
      - Entry:
        - Display: Export
        - Return: Export
      - Entry:
        - Display: Steward
        - Return: Steward
      - Entry:
        - Display: Admin
        - Return: Admin
  - LOV
    - Name: LOV_ACCESS_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Submitted
        - Return: Submitted
      - Entry:
        - Display: Pending Review
        - Return: Pending Review
      - Entry:
        - Display: Approved
        - Return: Approved
      - Entry:
        - Display: Rejected
        - Return: Rejected
      - Entry:
        - Display: Revoked
        - Return: Revoked
  - LOV
    - Name: LOV_ISSUE_SEVERITY
    - Type: Static
    - Entries:
      - Entry:
        - Display: Low
        - Return: Low
      - Entry:
        - Display: Medium
        - Return: Medium
      - Entry:
        - Display: High
        - Return: High
      - Entry:
        - Display: Critical
        - Return: Critical
  - LOV
    - Name: LOV_ISSUE_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Open
        - Return: Open
      - Entry:
        - Display: In Progress
        - Return: In Progress
      - Entry:
        - Display: Resolved
        - Return: Resolved
      - Entry:
        - Display: Closed
        - Return: Closed
  - LOV
    - Name: LOV_APPROVAL_REQUEST_TYPE
    - Type: Static
    - Entries:
      - Entry:
        - Display: Product Request
        - Return: Product Request
      - Entry:
        - Display: Access Request
        - Return: Access Request
      - Entry:
        - Display: Data Quality Issue
        - Return: Data Quality Issue
  - LOV
    - Name: LOV_APPROVAL_DECISION
    - Type: Static
    - Entries:
      - Entry:
        - Display: Pending
        - Return: Pending
      - Entry:
        - Display: Approved
        - Return: Approved
      - Entry:
        - Display: Rejected
        - Return: Rejected
      - Entry:
        - Display: More Information Needed
        - Return: More Information Needed
  - LOV
    - Name: LOV_TASK_RELATED_TYPE
    - Type: Static
    - Entries:
      - Entry:
        - Display: Data Product
        - Return: Data Product
      - Entry:
        - Display: Product Request
        - Return: Product Request
      - Entry:
        - Display: Access Request
        - Return: Access Request
      - Entry:
        - Display: Quality Issue
        - Return: Quality Issue
  - LOV
    - Name: LOV_TASK_STATUS
    - Type: Static
    - Entries:
      - Entry:
        - Display: Open
        - Return: Open
      - Entry:
        - Display: In Progress
        - Return: In Progress
      - Entry:
        - Display: Blocked
        - Return: Blocked
      - Entry:
        - Display: Completed
        - Return: Completed
  - LOV
    - Name: LOV_AUDIT_EVENT_TYPE
    - Type: Static
    - Entries:
      - Entry:
        - Display: Created
        - Return: Created
      - Entry:
        - Display: Updated
        - Return: Updated
      - Entry:
        - Display: Approved
        - Return: Approved
      - Entry:
        - Display: Rejected
        - Return: Rejected
      - Entry:
        - Display: Closed
        - Return: Closed
- Page Groups
  - Page Group
    - Name: Home
    - Description: Operational dashboard and quick access.
  - Page Group
    - Name: Data Products
    - Description: Data product records, product details, and product-dataset relationships.
  - Page Group
    - Name: Datasets
    - Description: Dataset catalog records and related governance activity.
  - Page Group
    - Name: Requests
    - Description: Product and access request intake and tracking.
  - Page Group
    - Name: Data Quality
    - Description: Dataset quality issue reporting and resolution tracking.
  - Page Group
    - Name: Approvals
    - Description: Approval queue and approval history management.
  - Page Group
    - Name: Tasks
    - Description: Delivery and governance work item tracking.
  - Page Group
    - Name: Audit
    - Description: Read-only audit event review.
- Menu
  - Menu Name: Navigation Menu
  - Entries:
    - Entry
      - Label: Home
      - Icon: fa-home
      - Action: Open Home
      - Target: Page 1
      - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Approver, Administrator
    - Entry
      - Label: Data Products
      - Icon: fa-cubes
      - Action: Open Data Products
      - Target: Page 2
      - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
    - Entry
      - Label: Datasets
      - Icon: fa-database
      - Action: Open Datasets
      - Target: Page 5
      - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
    - Entry
      - Label: Product Requests
      - Icon: fa-inbox
      - Action: Open Product Requests
      - Target: Page 8
      - Authorized Roles: Business Requester, Data Product Owner, Approver, Administrator
    - Entry
      - Label: Access Requests
      - Icon: fa-key
      - Action: Open Access Requests
      - Target: Page 11
      - Authorized Roles: Business Requester, Data Steward, Approver, Administrator
    - Entry
      - Label: Data Quality Issues
      - Icon: fa-exclamation-triangle
      - Action: Open Data Quality Issues
      - Target: Page 14
      - Authorized Roles: Business Requester, Data Steward, Administrator
    - Entry
      - Label: Approvals
      - Icon: fa-check-square-o
      - Action: Open Approvals
      - Target: Page 17
      - Authorized Roles: Approver, Administrator
    - Entry
      - Label: Tasks
      - Icon: fa-tasks
      - Action: Open Tasks
      - Target: Page 19
      - Authorized Roles: Data Product Owner, Data Steward, Administrator
    - Entry
      - Label: Audit Events
      - Icon: fa-history
      - Action: Open Audit Events
      - Target: Page 22
      - Authorized Roles: Administrator
- Breadcrumb
  - Name: Breadcrumb
  - Entries:
    - Entry
      - Name: Home
      - Page: Page 1
    - Entry
      - Name: Data Products
      - Page: Page 2
      - Parent Entry: Home
    - Entry
      - Name: Data Product Detail
      - Page: Page 3
      - Parent Entry: Data Products
    - Entry
      - Name: Datasets
      - Page: Page 5
      - Parent Entry: Home
    - Entry
      - Name: Dataset Detail
      - Page: Page 6
      - Parent Entry: Datasets
    - Entry
      - Name: Product Requests
      - Page: Page 8
      - Parent Entry: Home
    - Entry
      - Name: Product Request Detail
      - Page: Page 9
      - Parent Entry: Product Requests
    - Entry
      - Name: Access Requests
      - Page: Page 11
      - Parent Entry: Home
    - Entry
      - Name: Access Request Detail
      - Page: Page 12
      - Parent Entry: Access Requests
    - Entry
      - Name: Data Quality Issues
      - Page: Page 14
      - Parent Entry: Home
    - Entry
      - Name: Quality Issue Detail
      - Page: Page 15
      - Parent Entry: Data Quality Issues
    - Entry
      - Name: Approvals
      - Page: Page 17
      - Parent Entry: Home
    - Entry
      - Name: Tasks
      - Page: Page 19
      - Parent Entry: Home
    - Entry
      - Name: Task Detail
      - Page: Page 20
      - Parent Entry: Tasks
    - Entry
      - Name: Audit Events
      - Page: Page 22
      - Parent Entry: Home
- Lists
  - List
    - Name: Quick Actions
    - Entries
      - Entry
        - Label: Submit Product Request
        - Icon: fa-plus-circle
        - Action: Open Product Request Form
        - Target: Page 10
        - Authorized Roles: Business Requester, Data Product Owner, Administrator
        - Description: Create a new data product request.
      - Entry
        - Label: Submit Access Request
        - Icon: fa-key
        - Action: Open Access Request Form
        - Target: Page 13
        - Authorized Roles: Business Requester, Data Steward, Administrator
        - Description: Request access to a governed dataset.
      - Entry
        - Label: Report Quality Issue
        - Icon: fa-exclamation-triangle
        - Action: Open Quality Issue Form
        - Target: Page 16
        - Authorized Roles: Business Requester, Data Steward, Administrator
        - Description: Report a data quality issue for a dataset.
      - Entry
        - Label: Review Pending Approvals
        - Icon: fa-check-square-o
        - Action: Open Approvals
        - Target: Page 17
        - Authorized Roles: Approver, Administrator
        - Description: Review approval records awaiting a decision.
## Pages
### Page 1: Home
- Description: Operational dashboard for governed data product activity.
- Comments: Shows lifecycle counts and quick actions for common work.
- Pattern: dashboard
- Page Mode: standard
- Menu: true
- Page Group: Home
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Approver, Administrator
#### Regions
##### Region: Total Data Products KPI
- Comments: Counts all governed data product records.
- Position: body
- Colstart: 1
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Data Products
- Metric Icon: fa-cubes
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_data_products
```
  - Summary: Total number of data products.
- Columns:
  - Column Name: METRIC
    - Label: Total Data Products
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Open Product Requests KPI
- Comments: Counts product requests that are not completed or rejected.
- Position: body
- Colstart: 3
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Product Requests
- Metric Icon: fa-inbox
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_product_requests
where status not in ('Completed', 'Rejected')
```
  - Summary: Open product requests.
- Columns:
  - Column Name: METRIC
    - Label: Open Product Requests
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Pending Access Requests KPI
- Comments: Counts access requests waiting for a final decision.
- Position: body
- Colstart: 5
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Access Requests
- Metric Icon: fa-key
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_access_requests
where status not in ('Approved', 'Rejected', 'Revoked')
```
  - Summary: Pending access requests.
- Columns:
  - Column Name: METRIC
    - Label: Pending Access Requests
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Open Quality Issues KPI
- Comments: Counts unresolved data quality issues.
- Position: body
- Colstart: 7
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Quality Issues
- Metric Icon: fa-exclamation-triangle
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_quality_issues
where status in ('Open', 'In Progress')
```
  - Summary: Open quality issues.
- Columns:
  - Column Name: METRIC
    - Label: Open Quality Issues
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Pending Approvals KPI
- Comments: Counts approvals with a pending decision.
- Position: body
- Colstart: 9
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Approvals
- Metric Icon: fa-check-square-o
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_approvals
where decision = 'Pending'
```
  - Summary: Pending approvals.
- Columns:
  - Column Name: METRIC
    - Label: Pending Approvals
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Open Tasks KPI
- Comments: Counts open delivery and governance tasks.
- Position: body
- Colstart: 11
- Colspan: 2
- Component:
  - Component Type: Metric Card
- Metric Subtitle: Tasks
- Metric Icon: fa-tasks
- Metric Icon Style: subtle
- Data Source:
  - Type: SQL
  - SQL:
```sql
select count(*) as metric
from dpg_tasks
where status in ('Open', 'In Progress', 'Blocked')
```
  - Summary: Open tasks.
- Columns:
  - Column Name: METRIC
    - Label: Open Tasks
    - Datatype: number
    - Render As: metric
    - Visible: true
##### Region: Quick Actions
- Comments: Provides shortcuts for the most common user actions.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: List
  - Qualifier: Media List
### Page 2: Data Products
- Description: Searchable list of governed data products.
- Comments: Users can search, export, open details, and create data products.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Data Products
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Data Products Report
- Comments: Interactive report for data product records.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Data product list with lifecycle status, ownership, priority, and delivery dates.
- Data Source:
  - Type: Table
  - Name: DPG_DATA_PRODUCTS
  - Primary Keys: PRODUCT_ID
  - Order By: REQUESTED_ON desc
  - Summary: Data products available for governance and delivery tracking.
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_NAME
    - Label: Product Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
    - Column Context: Name of the data product.
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_OWNER
    - Label: Business Owner
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_PRODUCT_STATUS
    - Visible: true
    - Column Context LOV: LOV_PRODUCT_STATUS
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_PRIORITY
    - Visible: true
    - Column Context LOV: LOV_PRIORITY
  - Column Name: REQUESTED_BY
    - Label: Requested By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: TARGET_DELIVERY_DATE
    - Label: Target Delivery Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Render As: plainText
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 3
    - Link Passing: PRODUCT_ID
    - Link Target Items: P3_PRODUCT_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 4
    - Link Passing: PRODUCT_ID
    - Link Target Items: P4_PRODUCT_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Data Product Owner, Administrator
- Actions:
  - Action
    - Label: Create Data Product
    - Link To: Page 4
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Data Product Owner, Administrator
### Page 3: Data Product Detail
- Description: Detail page for a selected data product and related records.
- Comments: Shows selected product context with related requests, datasets, tasks, and audit events.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Data Products
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Data Product Context
- Comments: Displays the selected data product summary and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: PRODUCT_ID
  - SQL:
```sql
select dp.product_id,
       dp.product_name,
       dp.business_domain,
       dp.business_owner,
       dp.status,
       dp.priority,
       dp.requested_by,
       dp.requested_on,
       dp.target_delivery_date,
       dp.description
from dpg_data_products dp
where dp.product_id = to_number(:P3_PRODUCT_ID)
```
  - Summary: Selected data product context.
- Hidden Page Items: P3_PRODUCT_ID
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_NAME
    - Label: Product Name
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: BUSINESS_OWNER
    - Label: Business Owner
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REQUESTED_BY
    - Label: Requested By
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: TARGET_DELIVERY_DATE
    - Label: Target Delivery Date
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Render As: description
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 4
    - Link Type: primaryActions
    - Link Passing: PRODUCT_ID
    - Link Target Items: P4_PRODUCT_ID
    - Authorized Roles: Data Product Owner, Administrator
    - Label: Edit
##### Region: Product Requests in Data Product
- Comments: Lists product requests associated with the selected data product.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: REQUEST_ID
  - SQL:
```sql
select pr.request_id,
       pr.product_id,
       pr.request_title,
       pr.requester_name,
       pr.business_unit,
       pr.request_type,
       pr.status,
       pr.priority,
       pr.submitted_on,
       pr.due_date
from dpg_product_requests pr
where pr.product_id = to_number(:P3_PRODUCT_ID)
```
  - Summary: Product requests for the selected data product.
- Columns:
  - Column Name: REQUEST_ID
    - Label: Product Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TITLE
    - Label: Request Title
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_UNIT
    - Label: Business Unit
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: SUBMITTED_ON
    - Label: Submitted On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 9
    - Link Passing: REQUEST_ID
    - Link Target Items: P9_REQUEST_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Business Requester, Data Product Owner, Administrator
##### Region: Datasets in Data Product
- Comments: Lists datasets used by the selected data product.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: DATASET_ID
  - SQL:
```sql
select pd.product_id,
       pd.dataset_id,
       ds.dataset_name,
       ds.source_system,
       ds.business_domain,
       ds.classification,
       ds.steward_name,
       ds.refresh_frequency,
       ds.status,
       pd.usage_note
from dpg_product_datasets pd
join dpg_datasets ds on ds.dataset_id = pd.dataset_id
where pd.product_id = to_number(:P3_PRODUCT_ID)
```
  - Summary: Datasets related to the selected data product.
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: SOURCE_SYSTEM
    - Label: Source System
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: CLASSIFICATION
    - Label: Classification
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STEWARD_NAME
    - Label: Data Steward
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REFRESH_FREQUENCY
    - Label: Refresh Frequency
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: USAGE_NOTE
    - Label: Usage Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 6
    - Link Passing: DATASET_ID
    - Link Target Items: P6_DATASET_ID
    - Label: Dataset Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 23
    - Link Passing: PRODUCT_ID, DATASET_ID
    - Link Target Items: P23_PRODUCT_ID, P23_DATASET_ID
    - Label: Edit Relationship
    - Link Icon: fa-edit
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
- Actions:
  - Action
    - Label: Add Dataset Relationship
    - Link To: Page 23
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
##### Region: Tasks in Data Product
- Comments: Lists tasks directly related to the selected data product.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: TASK_ID
  - SQL:
```sql
select t.task_id,
       t.related_type,
       t.related_id,
       t.task_name,
       t.assigned_to,
       t.status,
       t.due_date
from dpg_tasks t
where t.related_type = 'Data Product'
  and t.related_id = to_number(:P3_PRODUCT_ID)
```
  - Summary: Tasks for the selected data product.
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: false
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 20
    - Link Passing: TASK_ID
    - Link Target Items: P20_TASK_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
##### Region: Audit Events in Data Product
- Comments: Lists audit events for the selected data product.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: AUDIT_ID
  - SQL:
```sql
select ae.audit_id,
       ae.event_type,
       ae.entity_name,
       ae.entity_id,
       ae.event_by,
       ae.event_on,
       ae.event_note
from dpg_audit_events ae
where ae.entity_name = 'Data Product'
  and ae.entity_id = to_number(:P3_PRODUCT_ID)
```
  - Summary: Audit events for the selected data product.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 4: Maintain Data Product
- Description: Create or edit a data product.
- Comments: Modal form for maintaining data product business fields.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Data Products
- Security Requirements:
  - Authorized Roles: Data Product Owner, Administrator
#### Regions
##### Region: Data Product Form
- Comments: Captures product name, ownership, lifecycle status, and delivery information.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_DATA_PRODUCTS
  - Primary Keys: PRODUCT_ID
  - Summary: Data product maintenance form.
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Page Item Name: P4_PRODUCT_ID
    - Render As: hidden
  - Column Name: PRODUCT_NAME
    - Label: Product Name
    - Datatype: varchar2
    - Page Item Name: P4_PRODUCT_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 200
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Page Item Name: P4_BUSINESS_DOMAIN
    - Render As: textField
    - Required: true
    - MaxLength: 100
  - Column Name: BUSINESS_OWNER
    - Label: Business Owner
    - Datatype: varchar2
    - Page Item Name: P4_BUSINESS_OWNER
    - Render As: textField
    - Required: true
    - MaxLength: 150
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P4_STATUS
    - Render As: selectList
    - LOV: LOV_PRODUCT_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Page Item Name: P4_PRIORITY
    - Render As: radioGroup
    - LOV: LOV_PRIORITY
    - Required: true
    - MaxLength: 20
  - Column Name: REQUESTED_BY
    - Label: Requested By
    - Datatype: varchar2
    - Page Item Name: P4_REQUESTED_BY
    - Render As: textField
    - MaxLength: 150
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Page Item Name: P4_REQUESTED_ON
    - Render As: datePicker
    - Required: true
  - Column Name: TARGET_DELIVERY_DATE
    - Label: Target Delivery Date
    - Datatype: date
    - Page Item Name: P4_TARGET_DELIVERY_DATE
    - Render As: datePicker
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Page Item Name: P4_DESCRIPTION
    - Render As: textarea
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 5: Datasets
- Description: Searchable catalog of governed datasets.
- Comments: Users can search, export, open details, and create dataset catalog records.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Datasets
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Datasets Report
- Comments: Interactive report for governed dataset catalog records.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Dataset catalog with classification, steward, refresh frequency, and lifecycle status.
- Data Source:
  - Type: Table
  - Name: DPG_DATASETS
  - Primary Keys: DATASET_ID
  - Summary: Governed datasets available for products, access requests, and quality tracking.
- Columns:
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: SOURCE_SYSTEM
    - Label: Source System
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: CLASSIFICATION
    - Label: Classification
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_DATASET_CLASSIFICATION
    - Visible: true
    - Column Context LOV: LOV_DATASET_CLASSIFICATION
  - Column Name: STEWARD_NAME
    - Label: Data Steward
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REFRESH_FREQUENCY
    - Label: Refresh Frequency
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_DATASET_STATUS
    - Visible: true
    - Column Context LOV: LOV_DATASET_STATUS
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Render As: plainText
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 6
    - Link Passing: DATASET_ID
    - Link Target Items: P6_DATASET_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 7
    - Link Passing: DATASET_ID
    - Link Target Items: P7_DATASET_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Data Steward, Administrator
- Actions:
  - Action
    - Label: Create Dataset
    - Link To: Page 7
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Data Steward, Administrator
### Page 6: Dataset Detail
- Description: Detail page for a selected governed dataset and related records.
- Comments: Shows selected dataset context with related products, access requests, and quality issues.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Datasets
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Dataset Context
- Comments: Displays selected dataset summary and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: DATASET_ID
  - SQL:
```sql
select ds.dataset_id,
       ds.dataset_name,
       ds.source_system,
       ds.business_domain,
       ds.classification,
       ds.steward_name,
       ds.refresh_frequency,
       ds.status,
       ds.description
from dpg_datasets ds
where ds.dataset_id = to_number(:P6_DATASET_ID)
```
  - Summary: Selected dataset context.
- Hidden Page Items: P6_DATASET_ID
- Columns:
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: SOURCE_SYSTEM
    - Label: Source System
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: CLASSIFICATION
    - Label: Classification
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: STEWARD_NAME
    - Label: Data Steward
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REFRESH_FREQUENCY
    - Label: Refresh Frequency
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Render As: description
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 7
    - Link Type: primaryActions
    - Link Passing: DATASET_ID
    - Link Target Items: P7_DATASET_ID
    - Authorized Roles: Data Steward, Administrator
    - Label: Edit
##### Region: Data Products in Dataset
- Comments: Lists data products that use the selected dataset.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: PRODUCT_ID
  - SQL:
```sql
select pd.product_id,
       pd.dataset_id,
       dp.product_name,
       dp.business_domain,
       dp.business_owner,
       dp.status,
       dp.priority,
       pd.usage_note
from dpg_product_datasets pd
join dpg_data_products dp on dp.product_id = pd.product_id
where pd.dataset_id = to_number(:P6_DATASET_ID)
```
  - Summary: Data products related to the selected dataset.
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_NAME
    - Label: Product Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_OWNER
    - Label: Business Owner
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: USAGE_NOTE
    - Label: Usage Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 3
    - Link Passing: PRODUCT_ID
    - Link Target Items: P3_PRODUCT_ID
    - Label: Product Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 23
    - Link Passing: PRODUCT_ID, DATASET_ID
    - Link Target Items: P23_PRODUCT_ID, P23_DATASET_ID
    - Label: Edit Relationship
    - Link Icon: fa-edit
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
##### Region: Access Requests in Dataset
- Comments: Lists access requests for the selected dataset.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: ACCESS_REQUEST_ID
  - SQL:
```sql
select ar.access_request_id,
       ar.dataset_id,
       ar.requester_name,
       ar.access_purpose,
       ar.access_level,
       ar.status,
       ar.requested_on,
       ar.approved_by,
       ar.decision_on
from dpg_access_requests ar
where ar.dataset_id = to_number(:P6_DATASET_ID)
```
  - Summary: Access requests for the selected dataset.
- Columns:
  - Column Name: ACCESS_REQUEST_ID
    - Label: Access Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ACCESS_PURPOSE
    - Label: Access Purpose
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ACCESS_LEVEL
    - Label: Access Level
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: APPROVED_BY
    - Label: Approved By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION_ON
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 12
    - Link Passing: ACCESS_REQUEST_ID
    - Link Target Items: P12_ACCESS_REQUEST_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Business Requester, Data Steward, Administrator
##### Region: Quality Issues in Dataset
- Comments: Lists quality issues for the selected dataset.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: ISSUE_ID
  - SQL:
```sql
select qi.issue_id,
       qi.dataset_id,
       qi.issue_title,
       qi.severity,
       qi.status,
       qi.reported_by,
       qi.reported_on,
       qi.assigned_to
from dpg_quality_issues qi
where qi.dataset_id = to_number(:P6_DATASET_ID)
```
  - Summary: Quality issues for the selected dataset.
- Columns:
  - Column Name: ISSUE_ID
    - Label: Quality Issue
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: ISSUE_TITLE
    - Label: Issue Title
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: SEVERITY
    - Label: Severity
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REPORTED_BY
    - Label: Reported By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REPORTED_ON
    - Label: Reported On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 15
    - Link Passing: ISSUE_ID
    - Link Target Items: P15_ISSUE_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Business Requester, Data Steward, Administrator
### Page 7: Maintain Dataset
- Description: Create or edit a governed dataset catalog record.
- Comments: Modal form for maintaining dataset metadata.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Datasets
- Security Requirements:
  - Authorized Roles: Data Steward, Administrator
#### Regions
##### Region: Dataset Form
- Comments: Captures dataset source, classification, steward, refresh, status, and description.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_DATASETS
  - Primary Keys: DATASET_ID
  - Summary: Dataset maintenance form.
- Columns:
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Page Item Name: P7_DATASET_ID
    - Render As: hidden
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Page Item Name: P7_DATASET_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 200
  - Column Name: SOURCE_SYSTEM
    - Label: Source System
    - Datatype: varchar2
    - Page Item Name: P7_SOURCE_SYSTEM
    - Render As: textField
    - MaxLength: 120
  - Column Name: BUSINESS_DOMAIN
    - Label: Business Domain
    - Datatype: varchar2
    - Page Item Name: P7_BUSINESS_DOMAIN
    - Render As: textField
    - MaxLength: 100
  - Column Name: CLASSIFICATION
    - Label: Classification
    - Datatype: varchar2
    - Page Item Name: P7_CLASSIFICATION
    - Render As: selectList
    - LOV: LOV_DATASET_CLASSIFICATION
    - Required: true
    - MaxLength: 40
  - Column Name: STEWARD_NAME
    - Label: Data Steward
    - Datatype: varchar2
    - Page Item Name: P7_STEWARD_NAME
    - Render As: textField
    - MaxLength: 150
  - Column Name: REFRESH_FREQUENCY
    - Label: Refresh Frequency
    - Datatype: varchar2
    - Page Item Name: P7_REFRESH_FREQUENCY
    - Render As: textField
    - MaxLength: 40
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P7_STATUS
    - Render As: selectList
    - LOV: LOV_DATASET_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: DESCRIPTION
    - Label: Description
    - Datatype: clob
    - Page Item Name: P7_DESCRIPTION
    - Render As: textarea
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 8: Product Requests
- Description: Searchable list of product requests.
- Comments: Users can submit, review, and open product request details.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Approver, Administrator
#### Regions
##### Region: Product Requests Report
- Comments: Interactive report for product request intake and tracking.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Product request list with related product, request type, priority, status, and due date.
- Data Source:
  - Type: SQL
  - Primary Keys: REQUEST_ID
  - SQL:
```sql
select pr.request_id,
       pr.product_id,
       dp.product_name,
       pr.request_title,
       pr.requester_name,
       pr.business_unit,
       pr.request_type,
       pr.status,
       pr.priority,
       pr.submitted_on,
       pr.due_date,
       pr.justification
from dpg_product_requests pr
left join dpg_data_products dp on dp.product_id = pr.product_id
```
  - Summary: Product requests with optional related product name.
- Columns:
  - Column Name: REQUEST_ID
    - Label: Product Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_NAME
    - Label: Related Data Product
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUEST_TITLE
    - Label: Request Title
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: BUSINESS_UNIT
    - Label: Business Unit
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_REQUEST_TYPE
    - Visible: true
    - Column Context LOV: LOV_REQUEST_TYPE
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_REQUEST_STATUS
    - Visible: true
    - Column Context LOV: LOV_REQUEST_STATUS
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_PRIORITY
    - Visible: true
    - Column Context LOV: LOV_PRIORITY
  - Column Name: SUBMITTED_ON
    - Label: Submitted On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: JUSTIFICATION
    - Label: Justification
    - Datatype: clob
    - Render As: plainText
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 9
    - Link Passing: REQUEST_ID
    - Link Target Items: P9_REQUEST_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 10
    - Link Passing: REQUEST_ID
    - Link Target Items: P10_REQUEST_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Business Requester, Data Product Owner, Administrator
- Actions:
  - Action
    - Label: Create Product Request
    - Link To: Page 10
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Business Requester, Data Product Owner, Administrator
### Page 9: Product Request Detail
- Description: Detail page for a selected product request.
- Comments: Shows request context with approval history, related tasks, and audit events.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Approver, Administrator
#### Regions
##### Region: Product Request Context
- Comments: Displays selected product request details and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: REQUEST_ID
  - SQL:
```sql
select pr.request_id,
       pr.product_id,
       dp.product_name,
       pr.request_title,
       pr.requester_name,
       pr.business_unit,
       pr.request_type,
       pr.status,
       pr.priority,
       pr.submitted_on,
       pr.due_date,
       pr.justification
from dpg_product_requests pr
left join dpg_data_products dp on dp.product_id = pr.product_id
where pr.request_id = to_number(:P9_REQUEST_ID)
```
  - Summary: Selected product request context.
- Hidden Page Items: P9_REQUEST_ID
- Columns:
  - Column Name: REQUEST_ID
    - Label: Product Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: PRODUCT_NAME
    - Label: Related Data Product
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: REQUEST_TITLE
    - Label: Request Title
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: BUSINESS_UNIT
    - Label: Business Unit
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: SUBMITTED_ON
    - Label: Submitted On
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: JUSTIFICATION
    - Label: Justification
    - Datatype: clob
    - Render As: description
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 10
    - Link Type: primaryActions
    - Link Passing: REQUEST_ID
    - Link Target Items: P10_REQUEST_ID
    - Authorized Roles: Business Requester, Data Product Owner, Administrator
    - Label: Edit
##### Region: Approvals in Product Request
- Comments: Lists approval decisions for the selected product request.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: APPROVAL_ID
  - SQL:
```sql
select a.approval_id,
       a.request_type,
       a.request_id,
       a.approver_name,
       a.decision,
       a.decision_date,
       a.comments
from dpg_approvals a
where a.request_type = 'Product Request'
  and a.request_id = to_number(:P9_REQUEST_ID)
```
  - Summary: Approval history for the selected product request.
- Columns:
  - Column Name: APPROVAL_ID
    - Label: Approval
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUEST_ID
    - Label: Request Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: APPROVER_NAME
    - Label: Approver
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION
    - Label: Decision
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION_DATE
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: COMMENTS
    - Label: Comments
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 18
    - Link Passing: APPROVAL_ID
    - Link Target Items: P18_APPROVAL_ID
    - Label: Edit Approval
    - Link Icon: fa-edit
    - Authorized Roles: Approver, Administrator
##### Region: Tasks in Product Request
- Comments: Lists tasks for the selected product request.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: TASK_ID
  - SQL:
```sql
select t.task_id,
       t.related_type,
       t.related_id,
       t.task_name,
       t.assigned_to,
       t.status,
       t.due_date
from dpg_tasks t
where t.related_type = 'Product Request'
  and t.related_id = to_number(:P9_REQUEST_ID)
```
  - Summary: Tasks for the selected product request.
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: false
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 20
    - Link Passing: TASK_ID
    - Link Target Items: P20_TASK_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Data Product Owner, Administrator
##### Region: Audit Events in Product Request
- Comments: Lists audit events for the selected product request.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: AUDIT_ID
  - SQL:
```sql
select ae.audit_id,
       ae.event_type,
       ae.entity_name,
       ae.entity_id,
       ae.event_by,
       ae.event_on,
       ae.event_note
from dpg_audit_events ae
where ae.entity_name = 'Product Request'
  and ae.entity_id = to_number(:P9_REQUEST_ID)
```
  - Summary: Audit events for the selected product request.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 10: Maintain Product Request
- Description: Create or edit a product request.
- Comments: Modal form for maintaining product request intake fields.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Product Owner, Administrator
#### Regions
##### Region: Product Request Form
- Comments: Captures request title, related product, requester, type, status, priority, dates, and justification.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_PRODUCT_REQUESTS
  - Primary Keys: REQUEST_ID
  - Summary: Product request maintenance form.
- Columns:
  - Column Name: REQUEST_ID
    - Label: Product Request
    - Datatype: number
    - Page Item Name: P10_REQUEST_ID
    - Render As: hidden
  - Column Name: PRODUCT_ID
    - Label: Related Data Product
    - Datatype: number
    - Page Item Name: P10_PRODUCT_ID
    - Render As: selectList
    - LOV: LOV_PRODUCTS
  - Column Name: REQUEST_TITLE
    - Label: Request Title
    - Datatype: varchar2
    - Page Item Name: P10_REQUEST_TITLE
    - Render As: textField
    - Required: true
    - MaxLength: 200
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Page Item Name: P10_REQUESTER_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 150
  - Column Name: BUSINESS_UNIT
    - Label: Business Unit
    - Datatype: varchar2
    - Page Item Name: P10_BUSINESS_UNIT
    - Render As: textField
    - MaxLength: 120
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Page Item Name: P10_REQUEST_TYPE
    - Render As: radioGroup
    - LOV: LOV_REQUEST_TYPE
    - Required: true
    - MaxLength: 40
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P10_STATUS
    - Render As: selectList
    - LOV: LOV_REQUEST_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: PRIORITY
    - Label: Priority
    - Datatype: varchar2
    - Page Item Name: P10_PRIORITY
    - Render As: radioGroup
    - LOV: LOV_PRIORITY
    - Required: true
    - MaxLength: 20
  - Column Name: SUBMITTED_ON
    - Label: Submitted On
    - Datatype: date
    - Page Item Name: P10_SUBMITTED_ON
    - Render As: datePicker
    - Required: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Page Item Name: P10_DUE_DATE
    - Render As: datePicker
  - Column Name: JUSTIFICATION
    - Label: Justification
    - Datatype: clob
    - Page Item Name: P10_JUSTIFICATION
    - Render As: textarea
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 11: Access Requests
- Description: Searchable list of dataset access requests.
- Comments: Users can submit and track access requests.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Approver, Administrator
#### Regions
##### Region: Access Requests Report
- Comments: Interactive report for dataset access requests.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Access request list with dataset, requester, access level, status, and decision details.
- Data Source:
  - Type: SQL
  - Primary Keys: ACCESS_REQUEST_ID
  - SQL:
```sql
select ar.access_request_id,
       ar.dataset_id,
       ds.dataset_name,
       ar.requester_name,
       ar.access_purpose,
       ar.access_level,
       ar.status,
       ar.requested_on,
       ar.approved_by,
       ar.decision_on
from dpg_access_requests ar
join dpg_datasets ds on ds.dataset_id = ar.dataset_id
```
  - Summary: Access requests with dataset name.
- Columns:
  - Column Name: ACCESS_REQUEST_ID
    - Label: Access Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ACCESS_PURPOSE
    - Label: Access Purpose
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ACCESS_LEVEL
    - Label: Access Level
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_ACCESS_LEVEL
    - Visible: true
    - Column Context LOV: LOV_ACCESS_LEVEL
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_ACCESS_STATUS
    - Visible: true
    - Column Context LOV: LOV_ACCESS_STATUS
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: APPROVED_BY
    - Label: Approved By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION_ON
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 12
    - Link Passing: ACCESS_REQUEST_ID
    - Link Target Items: P12_ACCESS_REQUEST_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 13
    - Link Passing: ACCESS_REQUEST_ID
    - Link Target Items: P13_ACCESS_REQUEST_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Business Requester, Data Steward, Administrator
- Actions:
  - Action
    - Label: Create Access Request
    - Link To: Page 13
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Business Requester, Data Steward, Administrator
### Page 12: Access Request Detail
- Description: Detail page for a selected access request.
- Comments: Shows access request context with approval history and audit events.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Approver, Administrator
#### Regions
##### Region: Access Request Context
- Comments: Displays selected access request details and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: ACCESS_REQUEST_ID
  - SQL:
```sql
select ar.access_request_id,
       ar.dataset_id,
       ds.dataset_name,
       ar.requester_name,
       ar.access_purpose,
       ar.access_level,
       ar.status,
       ar.requested_on,
       ar.approved_by,
       ar.decision_on
from dpg_access_requests ar
join dpg_datasets ds on ds.dataset_id = ar.dataset_id
where ar.access_request_id = to_number(:P12_ACCESS_REQUEST_ID)
```
  - Summary: Selected access request context.
- Hidden Page Items: P12_ACCESS_REQUEST_ID
- Columns:
  - Column Name: ACCESS_REQUEST_ID
    - Label: Access Request
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: ACCESS_PURPOSE
    - Label: Access Purpose
    - Datatype: varchar2
    - Render As: description
    - Visible: true
  - Column Name: ACCESS_LEVEL
    - Label: Access Level
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: APPROVED_BY
    - Label: Approved By
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: DECISION_ON
    - Label: Decision Date
    - Datatype: date
    - Render As: hidden
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 13
    - Link Type: primaryActions
    - Link Passing: ACCESS_REQUEST_ID
    - Link Target Items: P13_ACCESS_REQUEST_ID
    - Authorized Roles: Business Requester, Data Steward, Administrator
    - Label: Edit
##### Region: Approvals in Access Request
- Comments: Lists approval decisions for the selected access request.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: APPROVAL_ID
  - SQL:
```sql
select a.approval_id,
       a.request_type,
       a.request_id,
       a.approver_name,
       a.decision,
       a.decision_date,
       a.comments
from dpg_approvals a
where a.request_type = 'Access Request'
  and a.request_id = to_number(:P12_ACCESS_REQUEST_ID)
```
  - Summary: Approval history for the selected access request.
- Columns:
  - Column Name: APPROVAL_ID
    - Label: Approval
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REQUEST_ID
    - Label: Request Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: APPROVER_NAME
    - Label: Approver
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION
    - Label: Decision
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION_DATE
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: COMMENTS
    - Label: Comments
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 18
    - Link Passing: APPROVAL_ID
    - Link Target Items: P18_APPROVAL_ID
    - Label: Edit Approval
    - Link Icon: fa-edit
    - Authorized Roles: Approver, Administrator
##### Region: Audit Events in Access Request
- Comments: Lists audit events for the selected access request.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: AUDIT_ID
  - SQL:
```sql
select ae.audit_id,
       ae.event_type,
       ae.entity_name,
       ae.entity_id,
       ae.event_by,
       ae.event_on,
       ae.event_note
from dpg_audit_events ae
where ae.entity_name = 'Access Request'
  and ae.entity_id = to_number(:P12_ACCESS_REQUEST_ID)
```
  - Summary: Audit events for the selected access request.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 13: Maintain Access Request
- Description: Create or edit a dataset access request.
- Comments: Modal form for access request submission and decision fields.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Requests
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Administrator
#### Regions
##### Region: Access Request Form
- Comments: Captures dataset, requester, access purpose, requested level, status, and decision details.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_ACCESS_REQUESTS
  - Primary Keys: ACCESS_REQUEST_ID
  - Summary: Access request maintenance form.
- Columns:
  - Column Name: ACCESS_REQUEST_ID
    - Label: Access Request
    - Datatype: number
    - Page Item Name: P13_ACCESS_REQUEST_ID
    - Render As: hidden
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Page Item Name: P13_DATASET_ID
    - Render As: selectList
    - LOV: LOV_DATASETS
    - Required: true
  - Column Name: REQUESTER_NAME
    - Label: Requester
    - Datatype: varchar2
    - Page Item Name: P13_REQUESTER_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 150
  - Column Name: ACCESS_PURPOSE
    - Label: Access Purpose
    - Datatype: varchar2
    - Page Item Name: P13_ACCESS_PURPOSE
    - Render As: textarea
    - Required: true
    - MaxLength: 500
  - Column Name: ACCESS_LEVEL
    - Label: Access Level
    - Datatype: varchar2
    - Page Item Name: P13_ACCESS_LEVEL
    - Render As: radioGroup
    - LOV: LOV_ACCESS_LEVEL
    - Required: true
    - MaxLength: 40
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P13_STATUS
    - Render As: selectList
    - LOV: LOV_ACCESS_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: REQUESTED_ON
    - Label: Requested On
    - Datatype: date
    - Page Item Name: P13_REQUESTED_ON
    - Render As: datePicker
    - Required: true
  - Column Name: APPROVED_BY
    - Label: Approved By
    - Datatype: varchar2
    - Page Item Name: P13_APPROVED_BY
    - Render As: textField
    - MaxLength: 150
  - Column Name: DECISION_ON
    - Label: Decision Date
    - Datatype: date
    - Page Item Name: P13_DECISION_ON
    - Render As: datePicker
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 14: Data Quality Issues
- Description: Searchable list of reported data quality issues.
- Comments: Users can report, track, and resolve quality issues.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Data Quality
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Administrator
#### Regions
##### Region: Data Quality Issues Report
- Comments: Interactive report for quality issue tracking.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Quality issue list with dataset, severity, status, assignee, and resolution status.
- Data Source:
  - Type: SQL
  - Primary Keys: ISSUE_ID
  - SQL:
```sql
select qi.issue_id,
       qi.dataset_id,
       ds.dataset_name,
       qi.issue_title,
       qi.severity,
       qi.status,
       qi.reported_by,
       qi.reported_on,
       qi.assigned_to,
       qi.resolution_notes
from dpg_quality_issues qi
join dpg_datasets ds on ds.dataset_id = qi.dataset_id
```
  - Summary: Data quality issues with dataset name.
- Columns:
  - Column Name: ISSUE_ID
    - Label: Quality Issue
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ISSUE_TITLE
    - Label: Issue Title
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: SEVERITY
    - Label: Severity
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_ISSUE_SEVERITY
    - Visible: true
    - Column Context LOV: LOV_ISSUE_SEVERITY
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_ISSUE_STATUS
    - Visible: true
    - Column Context LOV: LOV_ISSUE_STATUS
  - Column Name: REPORTED_BY
    - Label: Reported By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: REPORTED_ON
    - Label: Reported On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: RESOLUTION_NOTES
    - Label: Resolution Notes
    - Datatype: clob
    - Render As: plainText
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 15
    - Link Passing: ISSUE_ID
    - Link Target Items: P15_ISSUE_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 16
    - Link Passing: ISSUE_ID
    - Link Target Items: P16_ISSUE_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Business Requester, Data Steward, Administrator
- Actions:
  - Action
    - Label: Create Quality Issue
    - Link To: Page 16
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Business Requester, Data Steward, Administrator
### Page 15: Quality Issue Detail
- Description: Detail page for a selected data quality issue.
- Comments: Shows quality issue context with related tasks and audit events.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Data Quality
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Administrator
#### Regions
##### Region: Quality Issue Context
- Comments: Displays selected quality issue details and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: ISSUE_ID
  - SQL:
```sql
select qi.issue_id,
       qi.dataset_id,
       ds.dataset_name,
       qi.issue_title,
       qi.severity,
       qi.status,
       qi.reported_by,
       qi.reported_on,
       qi.assigned_to,
       qi.resolution_notes
from dpg_quality_issues qi
join dpg_datasets ds on ds.dataset_id = qi.dataset_id
where qi.issue_id = to_number(:P15_ISSUE_ID)
```
  - Summary: Selected quality issue context.
- Hidden Page Items: P15_ISSUE_ID
- Columns:
  - Column Name: ISSUE_ID
    - Label: Quality Issue
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: DATASET_NAME
    - Label: Dataset Name
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: ISSUE_TITLE
    - Label: Issue Title
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: SEVERITY
    - Label: Severity
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REPORTED_BY
    - Label: Reported By
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: REPORTED_ON
    - Label: Reported On
    - Datatype: date
    - Render As: hidden
    - Visible: false
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: RESOLUTION_NOTES
    - Label: Resolution Notes
    - Datatype: clob
    - Render As: description
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 16
    - Link Type: primaryActions
    - Link Passing: ISSUE_ID
    - Link Target Items: P16_ISSUE_ID
    - Authorized Roles: Business Requester, Data Steward, Administrator
    - Label: Edit
##### Region: Tasks in Quality Issue
- Comments: Lists tasks for the selected quality issue.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: TASK_ID
  - SQL:
```sql
select t.task_id,
       t.related_type,
       t.related_id,
       t.task_name,
       t.assigned_to,
       t.status,
       t.due_date
from dpg_tasks t
where t.related_type = 'Quality Issue'
  and t.related_id = to_number(:P15_ISSUE_ID)
```
  - Summary: Tasks for the selected quality issue.
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: false
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 20
    - Link Passing: TASK_ID
    - Link Target Items: P20_TASK_ID
    - Label: Details
    - Link Icon: fa-search
    - Authorized Roles: Data Steward, Administrator
##### Region: Audit Events in Quality Issue
- Comments: Lists audit events for the selected quality issue.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: AUDIT_ID
  - SQL:
```sql
select ae.audit_id,
       ae.event_type,
       ae.entity_name,
       ae.entity_id,
       ae.event_by,
       ae.event_on,
       ae.event_note
from dpg_audit_events ae
where ae.entity_name = 'Quality Issue'
  and ae.entity_id = to_number(:P15_ISSUE_ID)
```
  - Summary: Audit events for the selected quality issue.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 16: Maintain Quality Issue
- Description: Create or edit a data quality issue.
- Comments: Modal form for reporting and resolving quality issues.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Data Quality
- Security Requirements:
  - Authorized Roles: Business Requester, Data Steward, Administrator
#### Regions
##### Region: Quality Issue Form
- Comments: Captures dataset, issue title, severity, status, reporter, assignment, and resolution notes.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_QUALITY_ISSUES
  - Primary Keys: ISSUE_ID
  - Summary: Quality issue maintenance form.
- Columns:
  - Column Name: ISSUE_ID
    - Label: Quality Issue
    - Datatype: number
    - Page Item Name: P16_ISSUE_ID
    - Render As: hidden
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Page Item Name: P16_DATASET_ID
    - Render As: selectList
    - LOV: LOV_DATASETS
    - Required: true
  - Column Name: ISSUE_TITLE
    - Label: Issue Title
    - Datatype: varchar2
    - Page Item Name: P16_ISSUE_TITLE
    - Render As: textField
    - Required: true
    - MaxLength: 200
  - Column Name: SEVERITY
    - Label: Severity
    - Datatype: varchar2
    - Page Item Name: P16_SEVERITY
    - Render As: radioGroup
    - LOV: LOV_ISSUE_SEVERITY
    - Required: true
    - MaxLength: 20
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P16_STATUS
    - Render As: selectList
    - LOV: LOV_ISSUE_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: REPORTED_BY
    - Label: Reported By
    - Datatype: varchar2
    - Page Item Name: P16_REPORTED_BY
    - Render As: textField
    - Required: true
    - MaxLength: 150
  - Column Name: REPORTED_ON
    - Label: Reported On
    - Datatype: date
    - Page Item Name: P16_REPORTED_ON
    - Render As: datePicker
    - Required: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Page Item Name: P16_ASSIGNED_TO
    - Render As: textField
    - MaxLength: 150
  - Column Name: RESOLUTION_NOTES
    - Label: Resolution Notes
    - Datatype: clob
    - Page Item Name: P16_RESOLUTION_NOTES
    - Render As: textarea
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 17: Approvals
- Description: Pending approval queue and approval history.
- Comments: Approvers can review pending approvals and inspect historical decisions.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Approvals
- Security Requirements:
  - Authorized Roles: Approver, Administrator
#### Regions
##### Region: Pending Approvals Report
- Comments: Shows approvals requiring a decision.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Pending approval queue filtered to approval records with decision Pending.
- Data Source:
  - Type: SQL
  - Primary Keys: APPROVAL_ID
  - SQL:
```sql
select a.approval_id,
       a.request_type,
       a.request_id,
       a.approver_name,
       a.decision,
       a.decision_date,
       a.comments
from dpg_approvals a
where a.decision = 'Pending'
```
  - Summary: Pending approvals queue.
- Columns:
  - Column Name: APPROVAL_ID
    - Label: Approval
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_APPROVAL_REQUEST_TYPE
    - Visible: true
    - Column Context LOV: LOV_APPROVAL_REQUEST_TYPE
  - Column Name: REQUEST_ID
    - Label: Request Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: APPROVER_NAME
    - Label: Approver
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION
    - Label: Decision
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_APPROVAL_DECISION
    - Visible: true
    - Column Context LOV: LOV_APPROVAL_DECISION
  - Column Name: DECISION_DATE
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: COMMENTS
    - Label: Comments
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 18
    - Link Passing: APPROVAL_ID
    - Link Target Items: P18_APPROVAL_ID
    - Label: Review
    - Link Icon: fa-edit
    - Authorized Roles: Approver, Administrator
- Actions:
  - Action
    - Label: Create Approval
    - Link To: Page 18
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Approver, Administrator
##### Region: Approval History Report
- Comments: Shows all approval decision records.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Full approval history for product, access, and governance requests.
- Data Source:
  - Type: Table
  - Name: DPG_APPROVALS
  - Primary Keys: APPROVAL_ID
  - Summary: Full approval history.
- Columns:
  - Column Name: APPROVAL_ID
    - Label: Approval
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_APPROVAL_REQUEST_TYPE
    - Visible: true
    - Column Context LOV: LOV_APPROVAL_REQUEST_TYPE
  - Column Name: REQUEST_ID
    - Label: Request Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: APPROVER_NAME
    - Label: Approver
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: DECISION
    - Label: Decision
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_APPROVAL_DECISION
    - Visible: true
    - Column Context LOV: LOV_APPROVAL_DECISION
  - Column Name: DECISION_DATE
    - Label: Decision Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: COMMENTS
    - Label: Comments
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 18
    - Link Passing: APPROVAL_ID
    - Link Target Items: P18_APPROVAL_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Approver, Administrator
### Page 18: Maintain Approval
- Description: Create or edit an approval decision.
- Comments: Modal form for updating approval decisions and comments.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Approvals
- Security Requirements:
  - Authorized Roles: Approver, Administrator
#### Regions
##### Region: Approval Form
- Comments: Captures approval request type, request reference, approver, decision, decision date, and comments.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_APPROVALS
  - Primary Keys: APPROVAL_ID
  - Summary: Approval maintenance form.
- Columns:
  - Column Name: APPROVAL_ID
    - Label: Approval
    - Datatype: number
    - Page Item Name: P18_APPROVAL_ID
    - Render As: hidden
  - Column Name: REQUEST_TYPE
    - Label: Request Type
    - Datatype: varchar2
    - Page Item Name: P18_REQUEST_TYPE
    - Render As: selectList
    - LOV: LOV_APPROVAL_REQUEST_TYPE
    - Required: true
    - MaxLength: 40
  - Column Name: REQUEST_ID
    - Label: Request Record
    - Datatype: number
    - Page Item Name: P18_REQUEST_ID
    - Render As: numberField
    - Required: true
  - Column Name: APPROVER_NAME
    - Label: Approver
    - Datatype: varchar2
    - Page Item Name: P18_APPROVER_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 150
  - Column Name: DECISION
    - Label: Decision
    - Datatype: varchar2
    - Page Item Name: P18_DECISION
    - Render As: selectList
    - LOV: LOV_APPROVAL_DECISION
    - Required: true
    - MaxLength: 30
  - Column Name: DECISION_DATE
    - Label: Decision Date
    - Datatype: date
    - Page Item Name: P18_DECISION_DATE
    - Render As: datePicker
  - Column Name: COMMENTS
    - Label: Comments
    - Datatype: varchar2
    - Page Item Name: P18_COMMENTS
    - Render As: textarea
    - MaxLength: 1000
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 19: Tasks
- Description: Searchable list of delivery and governance tasks.
- Comments: Users can track open tasks and update work item status.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Tasks
- Security Requirements:
  - Authorized Roles: Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Tasks Report
- Comments: Interactive report for all delivery and governance tasks.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Task list with related type, related record, assignee, status, and due date.
- Data Source:
  - Type: Table
  - Name: DPG_TASKS
  - Primary Keys: TASK_ID
  - Summary: Delivery and governance tasks.
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_TASK_RELATED_TYPE
    - Visible: true
    - Column Context LOV: LOV_TASK_RELATED_TYPE
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_TASK_STATUS
    - Visible: true
    - Column Context LOV: LOV_TASK_STATUS
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: plainText
    - Visible: true
- Links: 
  - Link:
    - Link To: Page 20
    - Link Passing: TASK_ID
    - Link Target Items: P20_TASK_ID
    - Label: Details
    - Link Icon: fa-search
  - Link:
    - Link To: Page 21
    - Link Passing: TASK_ID
    - Link Target Items: P21_TASK_ID
    - Label: Edit
    - Link Icon: fa-edit
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
- Actions:
  - Action
    - Label: Create Task
    - Link To: Page 21
    - slot: CREATE
    - Action Type: navigate
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
### Page 20: Task Detail
- Description: Detail page for a selected task.
- Comments: Shows task context with related audit events.
- Pattern: parent-child
- Page Mode: standard
- Menu: false
- Page Group: Tasks
- Security Requirements:
  - Authorized Roles: Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Task Context
- Comments: Displays selected task details and supports editing.
- Position: body
- Colstart: 1
- Colspan: 4
- Component:
  - Component Type: Content Row
  - Parent Child Role: Parent
- Data Source:
  - Type: SQL
  - Primary Keys: TASK_ID
  - SQL:
```sql
select t.task_id,
       t.related_type,
       t.related_id,
       t.task_name,
       t.assigned_to,
       t.status,
       t.due_date
from dpg_tasks t
where t.task_id = to_number(:P20_TASK_ID)
```
  - Summary: Selected task context.
- Hidden Page Items: P20_TASK_ID
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Render As: overline
    - Visible: true
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Render As: title2
    - Visible: true
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Render As: miscellaneous
    - Visible: true
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Render As: hidden
    - Visible: false
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Render As: hidden
    - Visible: false
- Links: 
  - Link:
    - Link To: Page 21
    - Link Type: primaryActions
    - Link Passing: TASK_ID
    - Link Target Items: P21_TASK_ID
    - Authorized Roles: Data Product Owner, Data Steward, Administrator
    - Label: Edit
##### Region: Audit Events in Task
- Comments: Lists audit events for the selected task.
- Position: body
- Colstart: 5
- Colspan: 8
- Component:
  - Component Type: Classic Report
  - Qualifier: Standard
  - Parent Child Role: Child
- Data Source:
  - Type: SQL
  - Primary Keys: AUDIT_ID
  - SQL:
```sql
select ae.audit_id,
       ae.event_type,
       ae.entity_name,
       ae.entity_id,
       ae.event_by,
       ae.event_on,
       ae.event_note
from dpg_audit_events ae
where ae.entity_name = 'Task'
  and ae.entity_id = to_number(:P20_TASK_ID)
```
  - Summary: Audit events for the selected task.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 21: Maintain Task
- Description: Create or edit a task.
- Comments: Modal form for delivery and governance task tracking.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Tasks
- Security Requirements:
  - Authorized Roles: Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Task Form
- Comments: Captures task relationship, name, assignment, status, and due date.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_TASKS
  - Primary Keys: TASK_ID
  - Summary: Task maintenance form.
- Columns:
  - Column Name: TASK_ID
    - Label: Task
    - Datatype: number
    - Page Item Name: P21_TASK_ID
    - Render As: hidden
  - Column Name: RELATED_TYPE
    - Label: Related Type
    - Datatype: varchar2
    - Page Item Name: P21_RELATED_TYPE
    - Render As: selectList
    - LOV: LOV_TASK_RELATED_TYPE
    - Required: true
    - MaxLength: 40
  - Column Name: RELATED_ID
    - Label: Related Record
    - Datatype: number
    - Page Item Name: P21_RELATED_ID
    - Render As: numberField
    - Required: true
  - Column Name: TASK_NAME
    - Label: Task Name
    - Datatype: varchar2
    - Page Item Name: P21_TASK_NAME
    - Render As: textField
    - Required: true
    - MaxLength: 200
  - Column Name: ASSIGNED_TO
    - Label: Assigned To
    - Datatype: varchar2
    - Page Item Name: P21_ASSIGNED_TO
    - Render As: textField
    - MaxLength: 150
  - Column Name: STATUS
    - Label: Status
    - Datatype: varchar2
    - Page Item Name: P21_STATUS
    - Render As: selectList
    - LOV: LOV_TASK_STATUS
    - Required: true
    - MaxLength: 30
  - Column Name: DUE_DATE
    - Label: Due Date
    - Datatype: date
    - Page Item Name: P21_DUE_DATE
    - Render As: datePicker
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
### Page 22: Audit Events
- Description: Searchable read-only audit event report.
- Comments: Administrators can filter, sort, search, and export important audit events.
- Pattern: report
- Page Mode: standard
- Menu: true
- Page Group: Audit
- Security Requirements:
  - Authorized Roles: Administrator
#### Regions
##### Region: Audit Events Report
- Comments: Interactive report for read-only audit event review.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Interactive Report
- Report Context: Audit events with event type, entity, user, event date, and note; report controls provide filtering by entity name, event type, user, and event date.
- Data Source:
  - Type: Table
  - Name: DPG_AUDIT_EVENTS
  - Primary Keys: AUDIT_ID
  - Order By: EVENT_ON desc
  - Summary: Read-only audit event history.
- Columns:
  - Column Name: AUDIT_ID
    - Label: Audit Event
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_TYPE
    - Label: Event Type
    - Datatype: varchar2
    - Render As: plainTextBasedOnLov
    - LOV: LOV_AUDIT_EVENT_TYPE
    - Visible: true
    - Column Context LOV: LOV_AUDIT_EVENT_TYPE
  - Column Name: ENTITY_NAME
    - Label: Entity Name
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: ENTITY_ID
    - Label: Entity Record
    - Datatype: number
    - Render As: hidden
    - Visible: false
  - Column Name: EVENT_BY
    - Label: Event By
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_ON
    - Label: Event On
    - Datatype: date
    - Render As: plainText
    - Visible: true
  - Column Name: EVENT_NOTE
    - Label: Event Note
    - Datatype: varchar2
    - Render As: plainText
    - Visible: true
### Page 23: Maintain Product Dataset Relationship
- Description: Create or edit the relationship between a data product and a dataset.
- Comments: Modal form for maintaining product-dataset usage notes.
- Pattern: modal-drawer
- Page Mode: modalDialog
- Menu: false
- Page Group: Data Products
- Security Requirements:
  - Authorized Roles: Data Product Owner, Data Steward, Administrator
#### Regions
##### Region: Product Dataset Relationship Form
- Comments: Captures the related data product, related dataset, and usage note.
- Position: body
- Colstart: 1
- Colspan: 12
- Component:
  - Component Type: Form
- Data Source:
  - Type: Table
  - Name: DPG_PRODUCT_DATASETS
  - Primary Keys: PRODUCT_ID, DATASET_ID
  - Summary: Product-dataset relationship maintenance form.
- Columns:
  - Column Name: PRODUCT_ID
    - Label: Data Product
    - Datatype: number
    - Page Item Name: P23_PRODUCT_ID
    - Render As: selectList
    - LOV: LOV_PRODUCTS
    - Required: true
  - Column Name: DATASET_ID
    - Label: Dataset
    - Datatype: number
    - Page Item Name: P23_DATASET_ID
    - Render As: selectList
    - LOV: LOV_DATASETS
    - Required: true
  - Column Name: USAGE_NOTE
    - Label: Usage Note
    - Datatype: varchar2
    - Page Item Name: P23_USAGE_NOTE
    - Render As: textarea
    - MaxLength: 500
- Actions:
  - Action
    - Label: Create
    - slot: CREATE
    - Action Type: submit
    - Process: Create
  - Action
    - Label: Apply Changes
    - slot: CHANGE
    - Action Type: submit
    - Process: Apply
  - Action
    - Label: Delete
    - slot: DELETE
    - Action Type: submit
    - Process: Delete
  - Action
    - Label: Cancel
    - slot: CLOSE
    - Action Type: navigate
    - Process: cancelDialog
