# Schema Metadata

## Table: DPG_DATA_PRODUCTS

Business-facing data products requested, governed, delivered, and tracked by the organization.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| PRODUCT_ID | NUMBER | No | Primary key. Unique identifier for the data product. |
| PRODUCT_NAME | VARCHAR2(200) | No | Name of the data product. |
| BUSINESS_DOMAIN | VARCHAR2(100) | No | Business domain the product belongs to. |
| BUSINESS_OWNER | VARCHAR2(150) | No | Person accountable for the data product. |
| STATUS | VARCHAR2(30) | No | Lifecycle status such as Draft, Under Review, Approved, In Development, Published, or Retired. |
| PRIORITY | VARCHAR2(20) | No | Priority such as Low, Medium, High, or Critical. |
| REQUESTED_BY | VARCHAR2(150) | Yes | Person who originally requested the data product. |
| REQUESTED_ON | DATE | No | Date the data product was requested. |
| TARGET_DELIVERY_DATE | DATE | Yes | Expected delivery date. |
| DESCRIPTION | CLOB | Yes | Business description of the data product. |

Primary key: `PRODUCT_ID`

---

## Table: DPG_DATASETS

Catalog of datasets that may support data products, access requests, and data quality tracking.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| DATASET_ID | NUMBER | No | Primary key. Unique identifier for the dataset. |
| DATASET_NAME | VARCHAR2(200) | No | Name of the dataset. |
| SOURCE_SYSTEM | VARCHAR2(120) | Yes | Source system where the dataset originates. |
| BUSINESS_DOMAIN | VARCHAR2(100) | Yes | Business domain the dataset belongs to. |
| CLASSIFICATION | VARCHAR2(40) | No | Data sensitivity classification such as Public, Internal, Confidential, or Restricted. |
| STEWARD_NAME | VARCHAR2(150) | Yes | Data steward responsible for the dataset. |
| REFRESH_FREQUENCY | VARCHAR2(40) | Yes | How often the dataset is refreshed. |
| STATUS | VARCHAR2(30) | No | Dataset lifecycle status. |
| DESCRIPTION | CLOB | Yes | Business description of the dataset. |

Primary key: `DATASET_ID`

---

## Table: DPG_PRODUCT_REQUESTS

Requests to create, enhance, change, or retire data products.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| REQUEST_ID | NUMBER | No | Primary key. Unique identifier for the product request. |
| PRODUCT_ID | NUMBER | Yes | Related data product. |
| REQUEST_TITLE | VARCHAR2(200) | No | Short title of the request. |
| REQUESTER_NAME | VARCHAR2(150) | No | Person submitting the request. |
| BUSINESS_UNIT | VARCHAR2(120) | Yes | Business unit making the request. |
| REQUEST_TYPE | VARCHAR2(40) | No | Type of request such as New Product, Enhancement, Change, or Retirement. |
| STATUS | VARCHAR2(30) | No | Request status such as Submitted, Under Review, Approved, Rejected, or Completed. |
| PRIORITY | VARCHAR2(20) | No | Request priority. |
| SUBMITTED_ON | DATE | No | Date the request was submitted. |
| DUE_DATE | DATE | Yes | Requested or expected due date. |
| JUSTIFICATION | CLOB | Yes | Business justification for the request. |

Primary key: `REQUEST_ID`

Foreign keys:
- `PRODUCT_ID` references `DPG_DATA_PRODUCTS.PRODUCT_ID`

---

## Table: DPG_PRODUCT_DATASETS

Relationship between data products and the datasets they use.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| PRODUCT_ID | NUMBER | No | Related data product. |
| DATASET_ID | NUMBER | No | Related dataset. |
| USAGE_NOTE | VARCHAR2(500) | Yes | Notes about how the dataset is used by the data product. |

Primary key: `PRODUCT_ID`, `DATASET_ID`

Foreign keys:
- `PRODUCT_ID` references `DPG_DATA_PRODUCTS.PRODUCT_ID`
- `DATASET_ID` references `DPG_DATASETS.DATASET_ID`

---

## Table: DPG_ACCESS_REQUESTS

Requests from users who need access to governed datasets.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| ACCESS_REQUEST_ID | NUMBER | No | Primary key. Unique identifier for the access request. |
| DATASET_ID | NUMBER | No | Dataset for which access is requested. |
| REQUESTER_NAME | VARCHAR2(150) | No | Person requesting access. |
| ACCESS_PURPOSE | VARCHAR2(500) | No | Business reason for requesting access. |
| ACCESS_LEVEL | VARCHAR2(40) | No | Requested access level such as Read, Export, Steward, or Admin. |
| STATUS | VARCHAR2(30) | No | Access request status. |
| REQUESTED_ON | DATE | No | Date access was requested. |
| APPROVED_BY | VARCHAR2(150) | Yes | Person who approved or rejected the request. |
| DECISION_ON | DATE | Yes | Date of the approval decision. |

Primary key: `ACCESS_REQUEST_ID`

Foreign keys:
- `DATASET_ID` references `DPG_DATASETS.DATASET_ID`

---

## Table: DPG_QUALITY_ISSUES

Data quality issues reported against cataloged datasets.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| ISSUE_ID | NUMBER | No | Primary key. Unique identifier for the quality issue. |
| DATASET_ID | NUMBER | No | Dataset with the reported quality issue. |
| ISSUE_TITLE | VARCHAR2(200) | No | Short title of the quality issue. |
| SEVERITY | VARCHAR2(20) | No | Business impact such as Low, Medium, High, or Critical. |
| STATUS | VARCHAR2(30) | No | Issue status such as Open, In Progress, Resolved, or Closed. |
| REPORTED_BY | VARCHAR2(150) | No | Person who reported the issue. |
| REPORTED_ON | DATE | No | Date the issue was reported. |
| ASSIGNED_TO | VARCHAR2(150) | Yes | Person assigned to resolve the issue. |
| RESOLUTION_NOTES | CLOB | Yes | Notes describing the resolution. |

Primary key: `ISSUE_ID`

Foreign keys:
- `DATASET_ID` references `DPG_DATASETS.DATASET_ID`

---

## Table: DPG_APPROVALS

Approval decisions for product, access, and governance requests.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| APPROVAL_ID | NUMBER | No | Primary key. Unique identifier for the approval record. |
| REQUEST_TYPE | VARCHAR2(40) | No | Type of request being approved. |
| REQUEST_ID | NUMBER | No | Identifier of the related request. |
| APPROVER_NAME | VARCHAR2(150) | No | Person responsible for the approval decision. |
| DECISION | VARCHAR2(30) | No | Approval outcome such as Pending, Approved, Rejected, or More Information Needed. |
| DECISION_DATE | DATE | Yes | Date the decision was made. |
| COMMENTS | VARCHAR2(1000) | Yes | Approval comments or decision notes. |

Primary key: `APPROVAL_ID`

---

## Table: DPG_TASKS

Work items used to deliver requests, resolve issues, and complete governance actions.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| TASK_ID | NUMBER | No | Primary key. Unique identifier for the task. |
| RELATED_TYPE | VARCHAR2(40) | No | Type of related entity, such as Product Request or Quality Issue. |
| RELATED_ID | NUMBER | No | Identifier of the related entity. |
| TASK_NAME | VARCHAR2(200) | No | Name or summary of the task. |
| ASSIGNED_TO | VARCHAR2(150) | Yes | Person assigned to complete the task. |
| STATUS | VARCHAR2(30) | No | Task status such as Open, In Progress, Blocked, or Completed. |
| DUE_DATE | DATE | Yes | Task due date. |

Primary key: `TASK_ID`

---

## Table: DPG_AUDIT_EVENTS

Traceable history of important user and system events.

| Column | Type | Nullable | Description |
|---|---:|---:|---|
| AUDIT_ID | NUMBER | No | Primary key. Unique identifier for the audit event. |
| EVENT_TYPE | VARCHAR2(60) | No | Type of event, such as Created, Updated, Approved, Rejected, or Closed. |
| ENTITY_NAME | VARCHAR2(60) | No | Name of the entity affected by the event. |
| ENTITY_ID | NUMBER | Yes | Identifier of the affected entity. |
| EVENT_BY | VARCHAR2(150) | Yes | User or process that performed the event. |
| EVENT_ON | DATE | No | Date and time the event occurred. |
| EVENT_NOTE | VARCHAR2(1000) | Yes | Additional audit event details. |

Primary key: `AUDIT_ID`