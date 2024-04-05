# OCICTL. A simple command-line tool for accessing databases and computing resources

OCI CLI offers a command line interface to work with OCI resources, like compute instances, databases and object storage. However, as it uses JSON as a main format of displaying information it requires an identifier of an OCI component instead of its display name. 

OCICTL is a tool to simplify the usage of OCI CLI. It displays information in a more readable text format and allows for providing display names of components instead of their OCI identifiers. It also makes it easier to manage composite services, like, for example, Base Database Service, which consists of multiple internal components (databases, nodes, etc).

Review Date: 28.01.2024

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
