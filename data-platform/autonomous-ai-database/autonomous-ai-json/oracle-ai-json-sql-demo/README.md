This repository contains scripts and data demonstrating how to work with JSON data in SQL
- JSON{}
- JSON_EXISTS
- partial and multivalue indexes

Prerequisites
- the following privileges and roles have to be granted to database user, which will be used:
    SODA_APP, CONNECT, RESOURCE, EXECUTE ON DBMS_CLOUD, EXECUTE ON DBMS_VECTOR
- before starting the demo there is need to execute json_arr_agg.sql script, as it creates JSON_ARRAY_AGG aggregate function, which is used in the demo

- contents
  - json_arr_agg.sql : script containing definition of JSON_ARRAY_AGG function
  - basic_demo.sql   : script demonstrating basic SQL JSON functionality (JSON Collection Tables/Views, JSON{}, JSON Path Expressions and JSON_EXISTS operator
  - indexes_demo.sql : script demonstrating creation and usage of partial and multivalue indexes
    

License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
