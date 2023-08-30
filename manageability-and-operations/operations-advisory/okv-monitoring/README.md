# OKV Monitoring 

This chapter provides a simple tool to monitor OKV.
It dumps all the snmp  info from any OKV as described in the documentation:
https://docs.oracle.com/en/database/oracle/key-vault/21.1/okvag/monitoring.html#GUID-C695162D-1BB4-4B86-889E-24322FD66EE7 

# Instructions

1. You need to install go 
2. Copy main.go file to any directory
3. Execute go mod init
4. Execute go mod tidy
5. Run the program as go run main.go -target="okv_ip" -Port=161 -UserName="okv_snmp_user" -AuthenticationPassphrase="okv_snmp_user" -PrivacyPassphrase="okv_snmp_user"

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.