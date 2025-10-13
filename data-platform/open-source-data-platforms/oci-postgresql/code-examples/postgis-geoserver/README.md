# Connect OCI PostgreSQL to Oracle Analytics Cloud

Reviewed: 30.09.2025

# When to use this asset?

Developers aiming to use PostGIS as an extension on OCI Database with PostgreSQL, and connecting, loading the spatial data into Geoserver.

# How to use this asset?

Open the postgis-geoserver.md file and follow the steps carefully.

# Pre-requisites:

- Create a VCN with public and private subnet
- Create an OCI PostgreSQL database instance in the private subnet, enable PostGIS extension in the configuration.
- Create a Linux instance in public subnet, same VCN
- Add port 5432 and 8080 to the private subnet security list

# License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.