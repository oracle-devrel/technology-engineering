# SQL Developer Web - Oracle Database Actions Access

Oracle Database Actions is formerly known as SQL Developer Web and is a web-based interface that uses Oracle REST Data Services to provide development, data studio, administration and monitoring features for Oracle Autonomous Database, Oracle Database Cloud Services and on-premises Oracle Database. Database Actions comes already configured, via ORDS, on Autonomous Database.

Reviewed: 10.06.2026

Database Actions, (here also abbreviated as DB Actions), runs in Oracle REST Data Services and access to it is provided through schema-based authentication. To access Database Actions, you must sign in as a database user whose schema has been enabled for Database Actions.

## User Authentication - prerequisites

User access to Database Actions is described as follows
- In Oracle Autonomous AI Database databases, the ADMIN user is pre-enabled;
- To enable another database user's schema it has to be [REST-enabled first](https://docs.oracle.com/en/database/oracle/sql-developer-web/sdwad/accessing-sql-developer-web.html#GUID-63D265FC-7500-4F88-8870-1C60E0A286FF). 

Key important information, when REST-enabling a schema user to authenticate via DB Actions are:
- <i><b>schema_name</i></b> : database Schema name (in uppercase)
- <i><b>schema_alias</i></b>: alias for the schema name which will appear in the URL the user will make use when authenticating to database via DB Actions.

<b>Note</b>: as a best practice, it is not recommended to name the schema alias as the schema name itself: this, as a security measure to avoid schema name exposure.

When signing in to Database Actions you can connect via ORDS Schema alias defined in the REST-enabling schema configuration as follows:
- <b>Database Actions Sign-in</b> page --> <b>Advanced</b> in the Path Field enter: <schema_alias>, then login and password of the database schema when <i>schema_name</i> and <i>schema_alias</i> differ (as recommended).

To connect to a given database in a multiple database pool scenario, when Database Actions is configured via an ORDS-Standalone, (or together with Tomcat/WebLogic), in a non-Autonomous AI Database (or ADB customer-managed configuration) the steps are as follows:
- <b>Database Actions Sign-in page</b> --> <b>Advanced</b> in the Path Field enter: 

    <i><database_pool_name>/<schema_name></i> 

    then schema name and password in the login-password portion.
<br>
<br>

# Useful Links
- [Signing-in to Database Actions](https://docs.oracle.com/en/database/oracle/sql-developer-web/25.4/sdweb/signing-database-actions.html)
- [Jeff Smith PM's Blog - SQL Developer Web](https://www.thatjeffsmith.com/sql-developer-web/)
<br>
<br>

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

