# Data Use Case Domains vs. User-Defined Types (UDTs)

> **Developer question:** If UDTs already let us create reusable types, why introduce Domains?

## 1. What is the new capability?

A **Data Use Case Domain** attaches reusable validation, display, ordering and annotation semantics to ordinary SQL values. `email email_domain` derives the scalar column type from the domain; `email VARCHAR2(255) DOMAIN email_domain` makes that association explicit.

## 2. How did we solve this before?

A **User-Defined Type (UDT)** can define an object with attributes, constructors and member methods. Object-valued columns are navigated through their attributes, rather than read as scalar values.

## 3. What is different?

**Object navigation is the visible difference:** `c.email.email_address` accesses an attribute of an object; `c.email` for a domain-backed column is already a scalar string. Domains do not add object identity, attributes or member methods. UDT specifications cannot declare a reusable `CHECK` on an attribute; table-level constraints can check object attributes. Domain constraints belong to the domain.

### Practical comparison

```sql
-- Object approach: the email column contains an object instance.
CREATE TYPE demo_email_obj AS OBJECT (email_address VARCHAR2(255));
/
CREATE TABLE demo_customers_obj (id NUMBER, email demo_email_obj);
INSERT INTO demo_customers_obj VALUES (1, demo_email_obj('a@example.com'));
SELECT c.email.email_address AS email_text FROM demo_customers_obj c;

-- Domain approach: the email column is still a VARCHAR2 scalar.
CREATE DOMAIN demo_email_domain AS VARCHAR2(255)
  CONSTRAINT demo_email_ck CHECK (INSTR(demo_email_domain, '@') > 1);
CREATE TABLE demo_customers_dom (id NUMBER, email demo_email_domain);
INSERT INTO demo_customers_dom VALUES (1, 'a@example.com');
SELECT c.email AS email_text FROM demo_customers_dom c;
-- Illustrative validation only: INSTR is not a complete email validator.
```

**How to explain it:** Ask: “What does the client receive?” In the object example it must handle a structured Oracle object and navigate `.email_address`; in the domain example it receives an ordinary string. Demonstrate the two `SELECT` statements side by side. Both can have table comments; domains additionally define reusable annotations.

## 4. What are the advantages and limitations?

**Domains:** simple SQL/client interoperability and shared business rules; changing widely used validation may require migration. **UDTs:** rich composite values and methods, but object construction, attribute navigation and driver mappings add complexity. Object methods are not equivalent to domain validation constraints.

## 5. When should developers adopt it?

Use domains for repeated scalar business concepts (email, percentage, currency code). Use UDTs for genuinely composite data and object behavior. Neither replaces the other; table `CHECK` constraints still work for table-specific rules.

## Key takeaway

**Domains reuse *meaning and rules* while preserving scalar access; UDTs reuse *object structure and behavior*.**

## Documentation — Oracle AI Database 26ai

- [CREATE DOMAIN](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/create-domain.html)
- [CREATE TYPE](https://docs.oracle.com/en/database/oracle/oracle-database/26/sqlrf/CREATE-TYPE.html)
