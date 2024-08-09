# OCI Data Flow Connection to ADB/PostgreSQL/OCI Streaming from OCI Data Science Notebook

Reviewed: 9.08.2024

# When to use this asset?

When you intend to connect/integrate Data Flow with the Autonomous Database/PostgreSQL or OCI Streaming. 

Supported scenarios:
- 1. Oracle Databases
    - 1. Autonomous Database with a Public Endpoint
    - 2. Autonomous Database with a Private Endpoint 
    - 3. Autonomous Database (Wallet Connection)
- 2. Non-Oracle Databases
    - 1. PostgreSQL (Spark)
- 3. Other Scenarios
    - 1. PostgreSQL to Autonomous
    - 2. Configuring OCI Streaming
    - 3. Consuming messages from Stream
    - 4. Producing messages to Stream

# How to use this asset?

- You can start creating your spark cluster and testing the connections directly in this notebook.
- There is a special place dedicated for storing your credentials (Testing purposes only!)
- Happy with the testing? Modify the code in this notebook and create your own OCI Data Flow application.
  
# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
