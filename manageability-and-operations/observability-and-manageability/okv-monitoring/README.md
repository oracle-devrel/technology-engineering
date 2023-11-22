
# Simple OKV modnitor wirtten in Go to get metrics from Oracle OKV Servers

## 1. INTRODUCTION

This utility can be used to connect metrics from OKV servers on-prem or in the OCI cloud

## 2. SOLUTION

Compile the utility with any Go compiler, then execute it to get the metrics

## 4. REQUIREMENTS

A compatible Go compiler

a very simple snmp okv crawler
it get the snmp published mib full crawling and print  it to the output
it translates the snmp operation described to https://docs.oracle.com/en/database/oracle/key-vault/21.1/okvag/monitoring.html#GUID-C695162D-1BB4-4B86-889E-24322FD66EE7
you need to install go 
copy this file to any directory
 execute go mod init
 execute go mod tidy
 run the program as go run main.go -target="okv_ip" -Port=numeric -UserName="" -AuthenticationPassphrase="" -PrivacyPassphrase=""

## 5.RELEASE NOTES

2023-22-11 initial release
  
# LICENSE

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/folder-structure/LICENSE) for more details.
