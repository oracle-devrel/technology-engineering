# JSON Relational Duality Views

JSON relational duality views give an abstraction layer on top of your data model. On top of a relational data model, you define JSON relational duality views, that provide a "document-like" view of the data. A JSON-relational duality view exposes data stored in relational database tables as JSON documents. The documents are materialized — generated on demand, not stored as such. Duality views give your data both a conceptual and an operational duality: it's organized both relationally and hierarchically. You can base different duality views on data that's stored in one or more of the same tables, providing different JSON hierarchies over the same, shared data.
This means that applications can access (create, query, modify) the same data as a set of JSON documents or as a set of related tables and columns, and both approaches can be employed at the same time. You can modify the data through the JRD view, just as if you were updating a JSON document .... and the relational data model is transparently updated.
Reversely, if you update your relational data model, the JSON representation is updated too, and the changes are made visible through the JSON Relational Duality View.

Reviewed: 30.10.2024

# Useful Links  

## Documentation
 
- [JSON-Relational Duality Developer's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/jsnvu/index.html)
- [SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/create-json-relational-duality-view.html)
- [Restrictions for JSON-Relational Duality Views](https://docs.oracle.com/en/database/oracle/oracle-database/23/rnfre/json-duality-views-restrictions.html)
- [oracle.com page](https://www.oracle.com/database/json-relational-duality/)

## Blogs

- [JSON Relational Duality: The Revolutionary Unification of Document, Object, and Relational Models](https://blogs.oracle.com/database/post/json-relational-duality-app-dev)


## LiveLabs   

- [all JSON Relational Duality LiveLabs](https://apexapps.oracle.com/pls/apex/f?p=133:100:105527022504069::::SEARCH:JSOn%20Duality) 

# Team Publications

## Blogs and Demo

- [Demo in folder demo running in a docker container](https://github.com/oracle-devrel/technology-engineering/tree/main/data-platform/core-converged-db/database-23c/json-relational-duality-views/demo)

## Videos

- [JSON Relational Duality Views](https://youtu.be/YMftyjrEpnU)
- [23ai blogs on blogs.oracle.com/coretec](https://blogs.oracle.com/coretec/category/cased-concurrency-control-rt-23ai)
 
# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
