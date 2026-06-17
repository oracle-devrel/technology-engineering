# Scripts

The directory contains reusable automation helpers that support recurring OCI and OpenShift operational tasks. It is intended to reduce manual, error-prone steps by providing consistent command sequences, validated defaults, and repeatable execution patterns. Content typically includes OCI focused snippets for common platform setup activities such as IAM preparation, compartment and policy creation, networking related commands, and baseline configuration checks. On the OpenShift side it may include manifests, helper commands, and post-install validation routines that standardize cluster configuration and verify expected outcomes. Scripts should remain small, readable, and parameter-driven, so they can be adapted across environments without hidden assumptions. Even when used manually, they serve as a reliable reference for “known good” procedures and verification steps.

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE.txt) for more details.