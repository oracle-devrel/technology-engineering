# Oracle XML DB

Oracle XML DB is a set of Oracle Database technologies related to high-performance handling of XML data: storing, generating, accessing, searching, validating, transforming, evolving, and indexing. It provides native XML support by encompassing both the SQL and XML data models in an interoperable way. Oracle XML DB is included as part of Oracle Database starting with Oracle9i Release 2 (9.2).

Oracle XML DB and the XMLType abstract data type make Oracle Database XML-aware. Storing XML data as an XMLType column or table lets the database perform XML-specific operations on the content. This includes XML validation and optimization. XMLType storage allows highly efficient processing of XML content in the database. Because there is a broad spectrum of XML usage, there is no one-size-fits-all storage model that offers optimal performance and flexibility for every use case. Oracle XML DB offers different storage models for XMLType, and several indexing methods appropriate to these different storage models. You can tailor performance and functionality to best fit the kind of XML data you have and the ways you use it. Oracle Database Release 23 introduced Transportable Binary XML (TBX) as a storage option, a variant built on top of CSX but without the dependency of a central dictionary.
Transportable Binary XML is the recommended method for storing XML documents natively in the Oracle Database beginning with Oracle Database 23. 

Reviewed: 2.05.2024

# Useful Links

## Documentation  
 
- [Oracle XML DB Release 23](https://docs.oracle.com/en/database/oracle/oracle-database/23/adxdb/index.html)
- [Oracle XML DB Release 19](https://docs.oracle.com/en/database/oracle/oracle-database/19/adxdb/index.html)
- [Oracle XMl DB on oracle.com](https://www.oracle.com/de/database/technologies/appdev/xmldb.html)
- [Introduction to Choosing an XMLType Storage Model and Indexing Approaches](https://docs.oracle.com/en/database/oracle/oracle-database/23/adxdb/choice-of-XMLType-storage-and-indexing.html#GUID-60132193-FCBB-4A7F-AA11-53CB660F67AF)
- [Oracle XML DB: Best Practices to Get Optimal Performance out of XML Queries](https://www.oracle.com/a/tech/docs/technical-resources/technicalreport-xmlquery.pdf)
- [Indexes for XMLType Data](https://docs.oracle.com/en/database/oracle/oracle-database/23/adxdb/indexes-for-XMLType-data.html#GUID-9F243764-7945-4EF4-9C94-624BE732708F)
- [Behavior Changes with Oracle Database 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/upgrd/oracle-database-changes-deprecations-desupports.html#GUID-A6776DEC-E7F3-4E9F-8751-29CB98704A31)
- [Oracle XML DB deprecated features with Oracle Database 23ai](https://docs.oracle.com/en/database/oracle/oracle-database/23/upgrd/oracle-database-changes-deprecations-desupports.html#GUID-2C4FCA8B-2617-49B9-89BD-A13A2BE42DCC)

## Blogs

- [Transportable Binary XML – modern XML document storage in Oracle Database 23c](https://blogs.oracle.com/database/post/transportable-binary-xml-in-oracle-database-23)
  
## Videos

- [Oracle XML DB in Oracle Database 19c and 23c](https://www.youtube.com/watch?v=s1Bc8KKLbpw)

## Oracle LiveSQL and LiveLabs Workshops

- [Oracle XML DB: Storing and Processing XML Documents (Tutorial)](https://livesql.oracle.com/apex/livesql/file/tutorial_HE5NRRMNBOHLLKRLZJU0VNRCB.html)
- [Oracle XML DB: store and process XML documents (LiveLab)](https://apexapps.oracle.com/pls/apex/f?p=133:180:110569535671696::::wid:3661)


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
