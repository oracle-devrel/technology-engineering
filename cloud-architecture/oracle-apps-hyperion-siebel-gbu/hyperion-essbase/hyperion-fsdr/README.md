# Oracle Hyperion EPM System Full Stack Disaster Recovery scripts

This GitHub repository provides custom scripts that serve as a starting point for creating your own scripts to use with OCI Full Stack Disaster Recovery for Hyperion applications.

Included scripts:
- start_services.ps1/sh - script to start all EPM System services, including WLS and OHS, on Windows (PowerShell) or Linux (Bash) compute
- stop_services.ps1/sh - script to start all EPM System services, including WLS and OHS, on Windows (PowerShell) or Linux (Bash) compute
- host_switch_failover.ps1/sh - script to update the host file after switching to the standby region. Windows (PowerShell) or Linux (Bash) script to be used in a user-defined plan group after starting the compute nodes in the standby region.
- host_switch_failback.ps1/sh - script to update the host file after switching from the standby region back to the primary region. Windows (PowerShell) or Linux (Bash) to be used in a user-defined plan group after starting the compute nodes in the primary region.

The complete tutorial is available here: [Automate Recovery for Oracle Enterprise Performance Management using OCI Full Stack Disaster Recovery](https://docs.oracle.com/en/learn/fsdr-integration-epm/)

Reviewed: 22.7.2024

# When to use this asset?

Use these scripts to customize your Full Stack Disaster Recovery plans and automate switchovers and failovers between OCI regions for EPM System applications.

# How to use this asset?

Use these scripts in FSDR user-defined plan groups [link](https://docs.oracle.com/en-us/iaas/disaster-recovery/doc/add-user-defined-plan-groups.html)

# Useful Links

OCI Full Stack Disaster Recovery documentation can be found [here](https://docs.oracle.com/en-us/iaas/disaster-recovery/index.html) .

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
