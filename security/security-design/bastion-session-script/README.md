# Bastion Session Script
 
This shell script can be used to easily connect to the OCI Bastion service based on temporary SSH keys. Authorization is granted based on OCI CLI authentication and OCI Permissions. For OCI CLI authentication both the use of exchanged API keys and session security tokens is supported. This script works also directly on OCI Cloud Shell, however only for Managed SSH Sessions since port forwarding is not supported on OCI Cloud Shell.
 
## When to use this asset?
 
Use this shell script if you want make use of OCI Bastions in a simple and secure way.
 
## How to use this asset?
 
**Usage: ./bastion-session.sh COMMAND [ARGS]...**

Example:

```text
./bastion-session.sh ssh -b bst001 -i instance-001 -u opc [-p <oci profile>]
./bastion-session.sh pf  -b bst001 -d 10.0.0.1 -e 3389 [-p <oci profile>] [-l <local port>] 
```

**Commands:**

  ssh : The session type "ssh" for Managed SSH session.

  pf  : The session type "pf" for Port Forwarding session.

**Arguments:**

| short | long                     | description |
|----|-----------------------------|---|
| -b | --bastion TEXT              | The Name of the Bastion to be used. [-b or -c is required]|
| -c | --bastion-ocid TEXT         | The OCID of the Bastion to be used. [-b or -c is required]|
| -i | --instance TEXT             | The name of the target instance to be used.|
| -j | --instance-ocid TEXT        | The OCID of the target instance to be used.|
| -u | --username TEXT             | The target resource username to be used. [default: opc]|
| -p | --profile TEXT              | The oci profile in the config file to load. [default: DEFAULT]|
| -s | --session TEXT              | The Bastion session name. [default: Bastion-Session]|
| -t | --ttl INTEGER               | The Bastion session time-to-live in seconds, minimum 1800, maximum 10800. [default: 10800]|
| -d | --destination-ip IP         | The destination IP Address to be used for Bastion session. [default: the first private ip address of instance]|
| -e | --destination-port INTEGER  | The destination port to be used for Port Forwarding session. [default: 22]|
| -l | --local-port INTEGER        | The local port to be used for Port Forwarding session. [defaults to same value as destination port]|
| -a | --key-alg TEXT              | The algorithm for the SSH key (ssh-keygen) to be used. [default: rsa]|
| -k | --key-size INTEGER          | The key size for the SSH key (ssh-keygen) to be used. [default: 4096]|
| -pr| --private-key TEXT          | The private key file to be used when not generating a temporary key pair. [by default not used]|
| -pu| --public-key TEXT           | The public key file to be used when not generating a temporary key pair. [by default not used]|
| -v | --verbose                   | Show verbose output for troubleshooting.|

Prerequisites:

- The OCI Command Line Interface (CLI) must be installed and configured.
  (See also [https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm])
- The jq commandline JSON processer must be installed.
  (See also [https://stedolan.github.io/jq])
 
# License
 
Copyright (c) 2023 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.