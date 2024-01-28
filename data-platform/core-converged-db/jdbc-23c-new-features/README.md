# OracleJDBC23cNewFeatures
This repo contains working code of examples demonstrating Reactive API support provided in Oracle JDBC Driver 23c
Before running the code there is need to provide in the code
1. database connection string - it should point into a 21c or 23c database
2. username
3. password

Also it is needed to create database structures (a table, a sequence and a trigger) used by this demo.
It can be done by executing jdb23cnfdemotable.sql script from, for example, SQL Developer, SQLcl or SQL*Plus
To build and run this project there's need to use Maven (POM file contains all the dependencies, including JDBC driver)


Review Date: 28.01.2024


### Documentation

- [Oracle JDBC23c Driver Developer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/jjdbc/index.html#Oracle%C2%AE-Database)

### Blogs

- [Oracle 23c JDBC driver: support for reactive programming](https://blogs.oracle.com/coretec/post/oracle-23c-jdbc-driver-support-for-reactive-programming)


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
