# Model Data Better

## Presenter purpose
Move the audience from *how data is stored* to *what the data means and which rules every application must honor*. The three features are complementary: Domains reuse value semantics, Annotations expose metadata, and Assertions enforce eligible cross-row or cross-table rules.

## Introduction — why developers should care
A `VARCHAR2(255)` column does not tell another developer that it is an email address. A `NUMBER` column does not explain a customer's credit policy. Those meanings often live in several applications, validation libraries, and documents. Every duplicated rule becomes harder to change consistently.

The opportunity is to let the schema express more of that intent so tools and applications have a common source of truth.

## The capabilities and what to notice

### Data Use Case Domains — reusable scalar semantics
Define a domain once for an email address and associate it with columns in different tables. Those columns retain ordinary scalar SQL access; unlike an object type, callers do not navigate an attribute such as `c.email.address`. A domain is especially useful when the same validation or display meaning occurs across customers, employees, and suppliers. It does not replace UDTs when the requirement is an object with methods and attributes.

### Annotations — metadata applications can discover
Attach application-facing labels or other metadata to supported schema objects and retrieve it through dictionary interfaces. An annotation is **descriptive**, not a security policy or a validation rule by itself. Think of schema-aware tools, low-code interfaces, and metadata-driven applications that need consistent descriptions rather than a separate spreadsheet of field meanings.

### Assertions — rules beyond a single row
A credit-limit policy can depend on both an order and its customer. Assertions let supported cross-row/table rules be declared and checked by the database, rather than implemented independently in each service. Distinguish these from ordinary CHECK constraints, which cover many simpler cases. Cross-table enforcement also deserves realistic workload testing.

## Demo coaching
In `model_data_better_demo.sqlnb`, define an email domain and show a valid and invalid value; inspect annotations; then use the customer-credit assertion to show the database enforcing the shared rule. Ask: *What happens if another application writes the same table tomorrow?* The database rule still applies.

The notebook demonstrates specific examples; do not imply that annotations automatically create an application UI or that every business rule is expressible as an assertion.

## Close-out — the memorable point
The schema is becoming a more useful contract. Developers can share validation, metadata, and cross-table rules without recreating them in every application. The practical starting point is a rule or field meaning already duplicated in several places.

## Presenter follow-up
For **Domains vs. UDTs**, stress scalar column access versus object-attribute navigation and different purposes. For **Domains vs. CHECK constraints**, stress central reuse versus a table-local rule. The existing comparison documents cover these questions; they are not part of the spoken walkthrough.

**Assets:** `model_data_better_demo.sqlnb`, `model_data_better_cleanup.sql`.
