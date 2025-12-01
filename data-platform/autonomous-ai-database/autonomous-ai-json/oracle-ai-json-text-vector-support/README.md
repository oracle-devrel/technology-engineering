This repository contains scripts and data demonstrating how to use Oracle Text and Oracle Vector Search with JSON data
- DATA directory stores sample data
- LABS directory stores two scripts :
   - demo.sql containing SQL code
   - demo.js containing NodeJS code, which can be executed in mongosh tool when connected to Oracle API for MongoDB

Prerequisites
- the following privileges and roles have to be granted to database user, which will be used:
    SODA_APP, CONNECT, RESOURCE, EXECUTE ON DBMS_CLOUD, EXECUTE ON DBMS_VECTOR
- all_MiniLM_L12_v2.onnx model, which is used to generate embeddings, it can be downloaded from the following URL :
  https://adwc4pm.objectstorage.us-ashburn-1.oci.customer-oci.com/p/eLddQappgBJ7jNi6Guz9m9LOtYe2u8LWY19GfgU8flFK4N9YgP4kTlrE9Px3pE12/n/adwc4pm/b/OML-Resources/o/all_MiniLM_L12_v2.onnx
- after downloading this model there is need to upload it to an Object Storage bucket
- sample data from DATA directory need to be uploaded to an Object Storage bucket
- Demonstration should be started from running SQL part,
  as demo.js assumes that all database structures (views, tables, etc) are already created.

License
Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.
