# AI JSON Cloud Demo

<Introduction>

Reviewed Date: 27.07.2026

# When to use this asset?

To demo the AI JSON capabilities.

# how to use this asset?

This repository contains demo presenting capabilities of Oracle Database related to processing external JSON data stored in Object Storage buckets.
It consists of the following files:
* utl_json_cloud.* - this is the definition of PL/SQL package UTL_JSON_CLOUD, which is used in the demo
    this package provides
      wrappers for credential creation procedures allowing to create a credential object in the same way regardless of the flavour of the database
      procedures automatizing creation of JSON collection views pointing to external JSON data
* demo.sql - demo presenting reading, importing, exporting and managing the external JSON data

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
