# Lock Free Reservation

In 23c there is a new feature called lock-free reservation (short for Lock-Free Column Value Reservations). It provides an in-database infrastructure for transactions operating on reservable columns to enable concurrent transactions to proceed without being blocked on updates made to reservable columns and issues automatic compensations for reservable updates of successful transactions in an aborted saga.

This new technology introduces the concept of a "journal table": instead of updating a row, we insert a new row in a journal table, avoiding locking the row we want to update. On commit, an exclusive lock is needed to actually update the row. But as it is only "on commit", the lock is released very quickly.

Especially online applications updating intensively and with huge concurrency, low cardinality tables can take advantage of this new feature.

Reviewed: 27.03.2024

# Useful Links

## Documentation

- [Database Concepts 23c](https://docs.oracle.com/en/database/oracle/oracle-database/23/cncpt/tables-and-table-clusters.html#GUID-7C6A8E8A-F634-4D0D-877A-F948D6101066)
- [Database Developer Guide 23c](https://docs.oracle.com/en/database/oracle/oracle-database/23/adfns/using-lock-free-reservation.html#GUID-60D87F8F-AD9B-40A6-BB3C-193FFF0E60BB) 


# Team Publications

- [Lock-free reservation in 23c: how to start with](https://blogs.oracle.com/coretec/post/lock-free-reservation-in-23c)
- [Lock-free reservation in 23c: scale your apps](https://blogs.oracle.com/coretec/post/lockfree-reservation-in-23c-scale-your-apps)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
