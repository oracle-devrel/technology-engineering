# Lock-Free Reservation

A Lock-Free Reservation allows multiple concurrent updates on a numeric column value to proceed without being blocked by uncommitted updates when adding or subtracting from the column value.

By avoiding the traditional locking mechanism during updates, this feature allows you to greatly improve on the user experience with reduced blocking in the presence of frequent concurrent updates to reservable columns. In previous releases, when a column value of a row is updated by adding or subtracting from it, all other updates to that row are blocked until the transaction is committed. With the introduction of the Lock-Free Reservation feature in Oracle Database 23ai, you can allow transactions 
to concurrently add or subtract from the same row’s reservable column without blocking each other by specifying the conditions for which the updates may proceed.
Especially online applications updating intensively and with huge concurrency, low cardinality tables can take advantage of this new feature.

Reviewed: 26.09.2024

# Useful Links

## Documentation

- [Database Concepts](https://docs.oracle.com/en/database/oracle/oracle-database/23/cncpt/tables-and-table-clusters.html#GUID-7C6A8E8A-F634-4D0D-877A-F948D6101066)
- [Database Developer Guide](https://docs.oracle.com/en/database/oracle/oracle-database/23/adfns/using-lock-free-reservation.html#GUID-60D87F8F-AD9B-40A6-BB3C-193FFF0E60BB)
- [SQL Language Reference](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/CREATE-TABLE.html#GUID-F9CE0CC3-13AE-4744-A43C-EAC7A71AAAB6)
- [Documentation: Guidelines and Restrictions for Lock-Free Reservation](https://docs.oracle.com/en/database/oracle/oracle-database/23/adfns/using-lock-free-reservation.html#GUID-B2C0C556-64D0-47B6-B8AE-C97AD56A0F96)


# Team Publications

## Blogs

- [Lock-free reservation: how to start with](https://blogs.oracle.com/coretec/post/lock-free-reservation-in-23c)
- [Lock-free reservation: scale your apps](https://blogs.oracle.com/coretec/post/lockfree-reservation-in-23c-scale-your-apps)

## Videos

- [23ai Playlist](https://www.youtube.com/playlist?list=PLHA__TOeNI7MNBND0JWQUqTYOQ1up-VHX)
- [Lock-Free Reservation](https://youtu.be/h6YvDoBfeyg)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
