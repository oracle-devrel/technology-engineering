# Vector Search using Sentence Transformer Embeddings
 
This document covers the topic of creating embeddings for Vector Search using the Sentence Transformer Embedding Model.

Reviewed: 2024.09.06
 

# When to use this asset?

In this asset we will explore how we can using the `oracledb` python SDK to interact with the Oracle Database 23ai with AI Vector Search Capabilities. We have created a table `simple_demo` within our Oracle Database and loaded 89 rows of sample text data into this table. Please refer to the SQL script `simple-demo-dataloading.sql` for the table creation and data loading statements which can be executed against our Oracle DB via SQLPlus or SQLDeveloper.

The following Notebook will go through reading in our sample data, using the open-source `all-MiniLM-L6-v2` Sentence Transformer to convert our text into a vector embedding and store the data back into our table via an update statement. We can then perform similarity search against our Vector DB to find the closest matched records based on our input data.


# How to use this asset?

This asset is provided as general purpose material. Please tailor the content according to your context and needs.


# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
