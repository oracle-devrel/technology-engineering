# JSON Relational Duality Views

JSON relational duality views give an abstraction layer on top of your data model. On top of a relational data model, you define JSON relational duality views, that provide a "document-like" view of the data. A JSON-relational duality view exposes data stored in relational database tables as JSON documents. The documents are materialized — generated on demand, not stored as such. Duality views give your data both a conceptual and an operational duality: it's organized both relationally and hierarchically. You can base different duality views on data that's stored in one or more of the same tables, providing different JSON hierarchies over the same, shared data.
This means that applications can access (create, query, modify) the same data as a set of JSON documents or as a set of related tables and columns, and both approaches can be employed at the same time. You can modify the data through the JRD view, just as if you were updating a JSON document .... and the relational data model is transparently updated.
Reversely, if you update your relational data model, the JSON representation is updated too, and the changes are made visible through the JSON Relational Duality View.

# Useful Links  

## Documentation
 
- [JSON-Relational Duality Developer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/jsnvu/index.html)
- [SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/create-json-relational-duality-view.html)
- [Restrictions for JSON-Relational Duality Views](https://docs.oracle.com/en/database/oracle/oracle-database/23/rnfre/json-duality-views-restrictions.html)

## Blogs

- [JSON Relational Duality: The Revolutionary Unification of Document, Object, and Relational Models](https://blogs.oracle.com/database/post/json-relational-duality-app-dev)
- [ODP.NET JSON Relational Duality and Oracle Database 23c Free](https://medium.com/oracledevs/odp-net-json-relational-duality-and-oracle-database-23c-free-9e4c03bdf41f)
- [Oracle Database 23c JSON Relational Duality Views REST APIs](https://www.thatjeffsmith.com/archive/2023/04/oracle-database-23c-json-relational-duality-views-rest-apis/)

## LiveLabs   

- [Exploring JSON Relational Duality Views in 23c Free using SQL](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3638&clear=RR,180&session=101604160358167)
- [AutoREST with JSON Relational Duality Views in 23c Free](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3634&clear=RR,180&session=101604160358167)
- [Exploring JSON Relational Duality Views in 23c Free with Java](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3637&clear=RR,180&session=101604160358167)
- [Schröedinger's Document: JSON Relational Duality Views in Oracle 23c](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3753&clear=RR,180&session=101604160358167)

# Team Publications 

- [Demo running in a docker container](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/database-23c/json-relational-duality-views/demo)
 
# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
