# Automating Security List Updates

Last reviewed: 2026-06-04

## Table of Contents

- [Automating Security List Updates](#automating-security-list-updates)
  - [Table of Contents](#table-of-contents)
- [Overview](#overview)
  - [The Problem We Solve](#the-problem-we-solve)
  - [Who Benefits?](#who-benefits)
  - [Business Impact](#business-impact)
  - [The Solution: OCI Security List CIDR Updater](#the-solution-oci-security-list-cidr-updater)
- [Real-World Use Cases](#real-world-use-cases)
  - [Update with current public IP (perfect for dynamic IPs)](#update-with-current-public-ip-perfect-for-dynamic-ips)
  - [Replace specific CIDR blocks across ingress rules](#replace-specific-cidr-blocks-across-ingress-rules)
  - [Preview changes safely](#preview-changes-safely)
- [Enterprise-Grade Reporting](#enterprise-grade-reporting)
- [Safety First Approach](#safety-first-approach)
- [Getting Started](#getting-started)
  - [1. Clone the repository](#1-clone-the-repository)
  - [2. Build the tool](#2-build-the-tool)
  - [3. Prepare your security list OCIDs](#3-prepare-your-security-list-ocids)
  - [4. Run your first update](#4-run-your-first-update)
  - [License](#license)

---

# Overview

This tool facilitates the update of OCI Security List across regions. Dealing with changing IP addresses and CIDR blocks can be time-consuming and error-prone. 

The OCI Security List CIDR Updater is an open-source tool that automates security list management with enterprise-grade features.

You can find it [here](https://github.com/eugsim1/OCI-Security-List-CIDR-Updater).

## The Problem We Solve

Managing OCI Security Lists manually presents several challenges:

- Time-consuming updates across multiple regions

- Human errors in CIDR block entries

- Inconsistent security rule management

- No audit trail of changes made

- Difficult rollbacks when needed

## Who Benefits?

- Cloud Engineers managing multiple OCI environments

- Security Teams ensuring consistent rule enforcement

- DevOps Teams automating infrastructure management

- Compliance Teams requiring detailed change audits

## Business Impact

- 90% reduction in time spent on security list updates

- Eliminated configuration errors

- Improved compliance with detailed audit trails

- Faster incident response with rollback capabilities

## The Solution: OCI Security List CIDR Updater

This Go-based tool provides comprehensive automation for your OCI security operations:

Key Features

- Multi-Region Support - Process security lists across all OCI regions simultaneously

- Flexible CIDR Replacement - Replace specific CIDR patterns or use your current public IP

- Dry Run Mode - Preview changes before applying them

- Comprehensive Reporting - Detailed CSV reports with full audit trails

- Rollback Capability - Automatic backup and restoration

- Batch Processing - Handle multiple security lists in one operation

# Real-World Use Cases

## Update with current public IP (perfect for dynamic IPs)

./oci_cidr_updater --update=both --use-current-ip --dry-run=false

## Replace specific CIDR blocks across ingress rules

./oci_cidr_updater --update=ingress --replace-cidr-file=old-cidr.txt --new-target-cidr-file=new-cidr.txt

## Preview changes safely

./oci_cidr_updater --update=both --dry-run=true

# Enterprise-Grade Reporting

The tool generates comprehensive CSV reports including:

- Security List OCIDs and regions

- Rule types (Ingress/Egress) and protocols

- Before/after CIDR values

- Operation status and timestamps

- Error messages for troubleshooting

# Safety First Approach

Built with operational safety in mind:

- Dry run by default - Prevents accidental changes

- Automatic backups - Before any modifications

- Error resilience - Continues processing if one list fails

- Validation - Checks OCID formats and permissions

# Getting Started

## 1. Clone the repository

git clone https://github.com/eugsim1/OCI-Security-List-CIDR-Updater

## 2. Build the tool

go build -o oci_cidr_updater

## 3. Prepare your security list OCIDs

echo "ocid1.securitylist.oc1.phx.aaaa..." > security_list_ocids.txt

## 4. Run your first update

./oci_cidr_updater --use-current-ip --dry-run=false

## License

Copyright (c) 2026 Oracle and/or its affiliates.  
Licensed under the Universal Permissive License (UPL), Version 1.0.  
See [LICENSE](LICENSE) for more details.  
