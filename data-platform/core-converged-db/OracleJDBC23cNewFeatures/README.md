# OracleJDBC23cNewFeatures
This repo contains working code of examples demonstrating Reactive API support provided in Oracle JDBC Driver 23c
Before running the code there is need to provide in the code
1. database connection string - it should point into a 21c or 23c database
2. username
3. password

Also it is needed to create database structures (a table, a sequence and a trigger) used by this demo.
It can be done by executing jdb23cnfdemotable.sql script from, for example, SQL Developer, SQLcl or SQL*Plus
To build and run this project there's need to use Maven (POM file contains all the dependencies, including JDBC driver)
