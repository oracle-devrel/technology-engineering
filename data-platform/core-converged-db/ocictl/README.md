# OCICTL. A simple command-line tool for accessing database and compute resources

OCI Cli offers a command line interface to work with OCI resources, like compute instances, databases and object storage. However - as it uses JSON as a main format of displaying information and - in some cases - requires providing an identifier of an OCI component instead of its display name, its direct using may be in such situations considered as not user friendly.

OCICTL is a tool simplifying using OCI Cli. It displays information in a more readable text format and allows for providing display names of components instead of their OCI identifiers. It also makes easier basic management of composite services, like, for example, Base Database Service, which consist of multiple internal components (databases, nodes, etc).


Review Date: 28.01.2024

## Documentation
- User Guide in the doc folder of this repository

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
