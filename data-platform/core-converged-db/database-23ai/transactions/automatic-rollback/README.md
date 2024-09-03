# Automatic Transaction Rollback Feature 

In Oracle Database 23c, apps can assign priorities (LOW, MEDIUM, HIGH) to transactions and configure how long a higher priority transaction should wait for row locks on a lower priority one. After the timeout, the blocking transaction is automatically rolled back and row locks are released so that the higher-priority transaction can proceed.
 
Reviewed: 27.03.2024

# Useful Links

## Documentation

- [23c Database Administrator's Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/admin/managing-transactions.html#GUID-14B028D0-48EA-4675-A113-48286AFCD8AB)
- [23c Database Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/TXN_PRIORITY.html#GUID-9E60833D-8B58-4E71-9CAF-60EB4C5648C7)
- [23c Database Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/TXN_AUTO_ROLLBACK_HIGH_PRIORITY_WAIT_TARGET.html#GUID-B835CD39-221B-40CF-8F59-098101FD2D74)
- [23c Database Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/refrn/TXN_AUTO_ROLLBACK_MODE.html#GUID-454171AA-19AA-44FC-A18D-0DE7C4676190)


# Team Publications

- [Automatic transaction rollback in 23c with high, medium and low-priority transactions](https://blogs.oracle.com/coretec/post/automatic-transaction-rollback-in-23c)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
