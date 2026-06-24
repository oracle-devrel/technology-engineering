# oracle-json sample NodeJS scripts presenting different features of MongoDB API and Oracle JSON Database
### 02_basic_demo.js 
This script contains examples describin Oracle API for MongoDB support for basic native MongoDB statements, like insert, insertMany, update, and find
### 03_expr.js
This script contains an example of using $sql operator allowing for executing SQL statements against an Oracle API for MongoDB instance and how it can be used as a replacement for $expr native MongoDB operator
### 04_mongo_views.js
This script contains an example proving that MongoDB views are fully supported by Oracle API for MongoDB, including their creation using native MongoDB commands
### 05_oracle_views.js
This script contains examples of using Oracle JSON Collection Views and JSON Duality Views in queries expressed by using native MongoDB commands.
examples cover creation, data loading (JSON Duality Views), querying as well as execution plans generation.
### 06_partial_indexes.js
This script contains example comparing native MongoDB partial indexes (not supported in exactly the same form by Oracle API for MongoDB) and Oracle function-based indexes, which can be used as a partial indexes replacements, but also offer full functionality of building indexing expressions, which are not limited to indexing only a part of the data.
### 07_ps_indexes.js
This script contains examples of using Oracle-specific Path-Subsetting indexes to increase the performance of MongoDB native commands. Examples cover creation such indexes by executing native MongoDB commands ($sql operator) as well as querying data and generating execution plans, which use such indexes
### 08_mv_indexes.js
This is the second script presenting another type of Oracle-specific indexes - Multivalue Indexes with examples of their creation and usage in MongoDB native queries, including displaying execution plans
### 09_transactions.js
This script presents full ACID transactions support provided by Oracle Database and Oracle API for MongoDB to MongoDB native applications: no limitations for size and time and availability even in case of a single-node/non-cluster/non-sharding architecture
