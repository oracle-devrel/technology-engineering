# in-memory-eligible-test 

The In-Memory Eligibility Test determines if a given workload would benefit or not benefit from Database In-Memory and assesses its eligibility for use of this feature. Eligibility is gauged by the percentage of analytical activity in the workload. 
If you are planning to implement Database In-Memory, you can use this tool to quickly identify and filter out databases that are ineligible You can then focus your Database In-Memory deployment on databases whose workload includes more intense analytic activity and 
could therefore benefit substantially. The higher the percentage of analytical activity in the workload, the more benefit you gain from Database In-Memory.
The In-Memory Eligibility Test is the IS_INMEMORY_ELIGIBLE procedure within the PL/SQL package DBMS_INMEMORY_ADVISE. This package is built into Oracle Database in 19.20. You do not need to download and install it.
 
## Useful Links

### Documentation

- [Database In-Memory Guide](https://docs.oracle.com/en/database/oracle/oracle-database/19/inmem/intro-to-in-memory-column-store.html#GUID-54764B12-9A27-405B-AD02-8BF5140CA078)

### Blogs

- [New In-Memory Eligibility Test](https://blogs.oracle.com/in-memory/post/inmemory-eligibility-test)


# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
