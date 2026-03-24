
Reviewed: 24.03.2026


# Creating a C3 Object Storage Backup Destination for ExaDB-C@C

**_Related article:_** [ExaDB-C@C Data Protection Supplementary Information Confluence page for ExaDB-C@C backup configuration and implementation details.](https://confluence.oraclecorp.com/confluence/x/brSdhwQ)

# Introduction

This article provides guidelines for the configuration of the C3 Object Storage Service to be used as a backup destination for databases residing on an ExaDB-C@C.

Aspects of this solution that are outside of the scope of this article include:

- Cost considerations
- I/O impact on the C3 storage services
- Backup landscape management, including offloading backups from object storage to external devices
- Capacity planning
- RMAN backup, restore and recovery operations

# Preparation

The C3 details that are required by the ExaDB-C@C backup administrator for successful configuration on the ExaDB-C@C are:

- C3 User OCID and username (email)
- Policies on C3 for using the object storage service in the way required
- API key and Fingerprint for the user
- CA Certificates for the C3 endpoint
- Tenancy OCID
- C3 endpoint (URL), Object Storage namespace and Bucket name

## Working environment

A workstation with access to the C3 public network and object storage endpoint is required. The two required activities include:

- [Obtaining the Certificate Authority Bundle](https://docs.oracle.com/en-us/iaas/compute-cloud-at-customer/cmn/obtaining-the-certificate-authority-bundle.htm) (contact your C3 system administrator for the bundle if required)
- A working installation of the OCI CLI. See [Working with the Command Line Interface (CLI)](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm) (contact your C3 system administrator for the parameter values if required)

> **Note**  
> All identifiable information has been obfuscated. Please consider the following when working with the OCI CLI snippets below:  
> - All variables enclosed in `< >` should be replaced by the actual values  
> - All return values enclosed in `< >` should be interpreted as the actual values in the applicable format  

The **/home/<user>/.oci/config** file should contain at least the following entries:

```ini
[DEFAULT]
user=<ocid>
fingerprint=<complete fingerprint>
tenancy=<ocid>
region=<region.<url>>
key_file=/home/<user>/.oci/obj_c3.pem
namespace=<C3 object namespace>
```

The following entries are appended to the `~/.bashrc` file (or the applicable `~/.<rc>` file of your current shell: i.e. `~/.cshrc`, `~/.zshrc`, `~/.tcshrc`, etc):

```bash
# OCI Environment variables
export OCI_CLI_CERT_BUNDLE=/home/<user>/.oci/cert-bundle.crt    # Required
export ExaComp=<ocid>                                           # For convenience when the compartment OCID is required in the OCI CLI command line parameters
```

Followed by a logout/login or:

```shell
$ . ~/.bashrc
$ env | grep -i oci
OCI_CLI_CERT_BUNDLE=/home/<user>/.oci/cert-bundle.crt
ExaComp=<ocid>
$ _
```

The following tests should be performed successfully as a minimum:

```shell
$ oci iam region list
{
  "data": [
    {
      "key": "<key>",
      "name": "<region name>"
    }
  ]
}
$ oci iam tenancy get --tenancy-id <ocid>
{
  "data": {
    "defined-tags": null,
    "description": null,
    "freeform-tags": null,
    "home-region-key": null,
    "id": "<ocid>",
    "name": "<tenancy name>",
    "upi-idcs-compatibility-layer-endpoint": null
  }
}
$ oci iam user get --user-id <ocid>
{
  "data": {
    "capabilities": null,
    "compartment-id": "<ocid>",
    "db-user-name": null,
    "defined-tags": {
      "Oracle-Tags": {
        "CreatedBy": "default/<admin>",
        "CreatedOn": "2025-04-08T17:14:29.217Z"
      }
    },
    "description": null,
    "email": "<email>",
    "email-verified": null,
    "external-identifier": null,
    "freeform-tags": {},
    "id": "<ocid>",
    "identity-provider-id": null,
    "inactive-status": null,
    "is-mfa-activated": null,
    "last-successful-login-time": null,
    "lifecycle-state": "ACTIVE",
    "name": "<user id>",
    "previous-successful-login-time": null,
    "time-created": "2025-04-08T17:14:29.245000+00:00"
  },
  "etag": "<etag>"
}
$ oci os ns get
{
  "data": "<C3 object namespace>"
}
$ _
```

## C3 Credentials

The object storage buckets can be deployed in either _existing_ or _dedicated_ compartments. The following policy statements need to be applied by the IAM administrator depending on the role and operational responsibility separation between the ExaDB-C@C backup and the C3 object storage administrator:

```text
Allow group <BackupAdmins> to manage buckets in compartment <BackupCompartment>
Allow group <BackupAdmins> to manage objects in compartment <BackupCompartment>
```

where:

- `manage`: All actions
- `buckets`: Bucket configuration
- `objects`: The stored files/objects

## Create Object Storage Bucket

Object storage buckets can be created by using either the Compute Enclave User Interface (CEUI) or the OCI CLI. Here is an OCI CLI example:

```shell
$ oci os bucket create --name ExaBackup --compartment-id $ExaComp 
{
  "data": {
    "approximate-count": null,
    "approximate-size": null,
    "auto-tiering": null,
    "compartment-id": "<ocid>",
    "created-by": "<ocid>",
    "defined-tags": {
      "Oracle-Tags": {
        "CreatedBy": "<user>",
        "CreatedOn": "2026-03-21T15:35:33.78Z"
      }
    },
    "etag": "<etag>",
    "freeform-tags": null,
    "id": "<ocid>",
    "is-read-only": null,
    "kms-key-id": null,
    "metadata": null,
    "name": "ExaBackup",
    "namespace": "<namespace>",
    "object-events-enabled": null,
    "object-lifecycle-policy-etag": null,
    "public-access-type": "NoPublicAccess",
    "replication-enabled": null,
    "storage-tier": "Standard",
    "time-created": "2026-03-21T15:35:33.814929+00:00",
    "versioning": "Disabled"
  },
  "etag": "<etag>"
}
$ _
```

Note the parameter:

```json
"public-access-type": "NoPublicAccess"
```

This value will only provide access to duly authorised credentials as stated above for the ExaDB-C@C backup administrator.

> **Note**
>
> Retention rules and object versioning may be applied. See [Defining Retention Rules](https://docs.oracle.com/en-us/iaas/compute-cloud-at-customer/cmn/object/defining-retention-rules.htm) and [Object Versioning](https://docs.oracle.com/en-us/iaas/compute-cloud-at-customer/cmn/object/managing-object-versioning.htm) in the documentation.

# Testing

In order to test the integrity of the configuration, tests may be performed using the following OCI CLI snippets:

```shell
$ oci os bucket list --compartment-id $ExaComp
{
  "data": [
    {
      "compartment-id": "<ocid>",
      "created-by": "<ocid>",
      "defined-tags": null,
      "etag": "<etag>",
      "freeform-tags": null,
      "name": "ExaBackup",
      "namespace": "<namespace>",
      "time-created": "2026-03-21T15:35:33.814929+00:00"
    }
  ]
}
$ oci os object put --bucket-name ExaBackup --file config
Uploading object  [####################################]  100%
{
  "etag": "<etag>",
  "last-modified": "2026-03-22T08:52:47.276169Z",
  "opc-content-md5": "QuvNSbLebViKpnxIA6waUg=="
}
$ oci os object list --bucket-name ExaBackup
{
  "data": [
    {
      "archival-state": null,
      "etag": "<etag>",
      "md5": "QuvNSbLebViKpnxIA6waUg==",
      "name": "config",
      "size": 633,
      "storage-tier": "Standard",
      "time-created": "2026-03-22T08:52:46.970582+00:00",
      "time-modified": "2026-03-22T08:52:47.276169+00:00"
    }
  ],
  "prefixes": []
}
$ oci os object delete --bucket-name ExaBackup --name config
Are you sure you want to delete this resource? [y/N]: y
$ oci os object list --bucket-name ExaBackup
{
  "prefixes": []
}
$ _
```

The configuration is now complete and the object storage may be handed over to the ExaDB-C@C backup administrator for testing and implementation.



## License
Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.
