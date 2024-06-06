
## Overview
This section covers the new features introduced in the Oracle Database 23ai release, focusing on enhancements and functionalities in SQL for application development.

## Features

### Aggregation over INTERVAL Data Types
- **Description**: Pass INTERVAL data types to SUM and AVG aggregate functions.
- **Example**: ```sqlSELECT SUM(interval_column) FROM table_name;`

### Client Describe Call Support for Tag Options
- **Description**: Store and retrieve metadata about database objects using annotations.
- **Example**: `ALTER TABLE table_name ANNOTATE 'key' = 'value';`

### DEFAULT ON NULL for UPDATE Statements
- **Description**: Define columns as DEFAULT ON NULL for update operations.
- **Example**: `UPDATE table_name SET column_name = DEFAULT ON NULL WHERE condition;`

### Data Quality Operators
- **Description**: Introduces PHONIC_ENCODE and FUZZY_MATCH operators for string matching.
- **Example**: `SELECT PHONIC_ENCODE('word'), FUZZY_MATCH('string1', 'string2') FROM dual;`

### Data Use Case Domains
- **Description**: Define and apply constraints for common values like credit card numbers.
- **Example**: `CREATE DOMAIN email_domain AS VARCHAR2(255) CHECK (REGEXP_LIKE(value, '^[\w._%+-]+@[\w.-]+\.[a-zA-Z]{2,}$'));`

### Direct Joins for UPDATE and DELETE Statements
- **Description**: Join target tables in UPDATE and DELETE statements using the FROM clause.
- **Example**: `UPDATE table1 SET column1 = table2.column2 FROM table2 WHERE table1.id = table2.id;`

### GROUP BY Column Alias or Position
- **Description**: Use column aliases or SELECT item positions in GROUP BY clauses.
- **Example**: `SELECT column1 AS col1, SUM(column2) FROM table_name GROUP BY col1;`

### IF [NOT] EXISTS Syntax Support
- **Description**: Support for IF EXISTS and IF NOT EXISTS syntax in DDL operations.
- **Example**: `CREATE TABLE IF NOT EXISTS table_name (column1 datatype);`

### New Database Role for Application Developers
- **Description**: Introduces DB_DEVELOPER_ROLE with necessary privileges for developers.
- **Example**: `GRANT DB_DEVELOPER_ROLE TO user_name;`

### Oracle SQL Access to Kafka
- **Description**: Efficient access to data streams from Apache Kafka and OCI Streaming Service.
- **Example**: `SELECT * FROM kafka_table WHERE topic = 'topic_name';`

### SELECT Without FROM Clause
- **Description**: Run SELECT expression-only queries without a FROM clause.
- **Example**: `SELECT 1+1;`

### SQL BOOLEAN Data Type
- **Description**: Supports ISO SQL standard-compliant BOOLEAN data type.
- **Example**: `CREATE TABLE table_name (column1 BOOLEAN);`

### SQL UPDATE RETURN Clause Enhancements
- **Description**: Enhanced RETURNING INTO clause for reporting old and new values.
- **Example**: `UPDATE table_name SET column1 = 'new_value' RETURNING column1 INTO :old_value;`

### Schema Annotations
- **Description**: Store and retrieve metadata about database objects using name-value pairs.
- **Example**: `ANNOTATE SCHEMA 'key' = 'value';`

### Table Value Constructor
- **Description**: Supports VALUES clause for SELECT, INSERT, and MERGE statements.
- **Example**: `INSERT INTO table_name VALUES (1, 'value');`

### Ubiquitous Search With DBMS_SEARCH Packages
- **Description**: Index multiple schema objects for full-text search using DBMS_SEARCH.
- **Example**: `EXEC DBMS_SEARCH.CREATE_INDEX('index_name', 'table_name');`

## Release Informationnnn
- **Version**: 23ai
- **Applicable Offerings**: All Oracle Database offerings
For more detailed information, please visit the [Oracle Database Features](https://apex.oracle.com/database-features/) page.

