This repo contains some simple Java console application, which uses MongoDB Reactive Driver to perform some operations against 
Oracle Database with Oracle API for MongoDB enabled

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.

# Requirements
1. Java JDK 21
2. Oracle Database 23ai (any release) with Oracle API MongoDB configured and enabled
3. ORADEV schema in the database (as it is used by the code)
4. EMPLOYEES table installed in ORADEV schema. It can be taken from HR sample schema
5. Sample collections in ORADEV schema
    EMP_JSON_VIEW, which can be created as a collection view using the following SQL statement :
    create json collection view EMP_JSON_VIEW
    as
    select JSON{*}
    from EMPLOYEES;
6. COLORS json collection, which can be created as JSON collection table, using the following SQL statement :
   create json collection table COLORS;

7. It is required also to set DB_URI environment variable to connect string pointing to Oracle API MongoDB instance, which will be used. 

# Notes
1. Please, note, that this application uses Reactive MongoDB driver, which allows for executing database operations in async mode.
2. Also - to perform database operation in reactive mode (which is, in fact, a client-side emulation of asynchronous mode).
