# Priority Transactions

A transaction acquires a row lock for each row modified by one of the following statements: INSERT, UPDATE, DELETE, MERGE, and SELECT ... FOR UPDATE. The row lock exists until the transaction commits or rolls back.
Transactions can hold row locks for a long duration in certain cases. Traditionally, when a transaction is blocked on a row lock by another transaction for a long time, the database administrator manually terminates the blocking transaction by using the ALTER SYSTEM KILL SESSION command. 

Starting with Oracle Database release 23, applications can assign priorities (LOW, MEDIUM, HIGH) to transactions. If a low-priority transaction blocks a high-priority transaction on row locks, Oracle database will automatically roll back the low-priority transaction to let the high-priority transaction(s) progress. The database administrator needs to configure the time after which the low-priority transaction is rolled back.
 
Reviewed: 08.05.2024

# Useful Links

## Documentation

- [Database Administrator’s Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/admin/managing-transactions.html#GUID-8B71D725-24E9-4AE1-B9FA-BAC291923EAC)
- [Database Reference TXN_PRIORTY](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/TXN_PRIORITY.html)
- [Database Reference PRIORITY_TXNS_HIGH_WAIT_TARGET](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/PRIORITY_TXNS_HIGH_WAIT_TARGET.html#GUID-B835CD39-221B-40CF-8F59-098101FD2D74)
- [Database Reference PRIORITY_TXNS_MEDIUM_WAIT_TARGET](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/PRIORITY_TXNS_MEDIUM_WAIT_TARGET.html#GUID-7FC69016-983B-460E-A296-0B41247F1A52)
- [Database Reference PRIORITY_TXNS_MODE](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/PRIORITY_TXNS_MODE.html#GUID-454171AA-19AA-44FC-A18D-0DE7C4676190)


# Team Publications

- [Priority Transactions with high, medium and low priority](https://blogs.oracle.com/coretec/post/automatic-transaction-rollback-in-23c)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
