# Identity Token Propagation Script

## Overview

A colleague of mine posted an [article](https://www.ateam-oracle.com/post/authentication-and-user-propagation-for-api-calls) explaining a method for propagating identity using tokens when using Oracle Identity Cloud Service (IDCS) or Oracle Cloud Infrastructure (OCI) IAM domains. In this article, Olaf used the OAuth User Assertion flow in which a local, trusted custom application generates local identity tokens for its authenticated users. These tokens (either JWT or SAML) are the passed to IAM where it exchanges them for an IAM-issued token, which is then used to access an IAM integrated backend service. In the article's example, Oracle SaaS is used as the example endpoint.

I have found that I had a need to test this scenario quite a bit recently, so decided to script it. Here is the completed script, which includes the following features:

- Generation of local JWT or SAML tokens
- Storage of private keys locally or within OCI Vault
- Parameterised configuration to enable easy change for testing in different environments

## Pre-requisites

In order to use this script there are a few pre-requisites that must be met:

- Python 3.8 or later installed
- Python JWT installed
- A public/private key pair and digital certificate that can be used to sign your local tokens
    - The private key should be in PEM format
    - The public key, private key, and certificate files should be placed in a folder called `keys`
- OCI CLI installed and configured (if you are planning to use OCI Vault to store the private key)
- Access to an OCI environment with either IDCS or OCI IAM Domains
- An IAM-integrated backend service against which you can test API access (e.g., Oracle Integration Cloud)
- Within OCI IAM, the following configuration that must be completed:
    - A trusted application that is configured to trust your locally issued tokens
    - The IAM-integrated PaaS application configured
    - Test user accounts configured with an application role for the target PaaS service

Before testing the script, the target resource and IAM must be configured within your OCI tenancy. 

Refer to the [Setup Guide](/oic-target-setup.md) for details of how to configure IAM and Oracle Integration Cloud for this script.

## Running the Script

To execute the test, import the Python modules into your Python environment using the `requirements.txt` file, the run `run_demo.py`.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See LICENSE for more details.