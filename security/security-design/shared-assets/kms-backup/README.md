# OCI Vault software key backup

Owner: Inge Os

OCI Vault supports several types of keys, two HSM based, and software based.

Most services in Oracle OCI with encryption offers two types of encryption key management, Oracle Managed keys or Customer Managed keys.

Some common main requirements most often seen in various cyber security frameworks typically are:
-	Separation of Duty, key administration is separated from service management. Typical for Oracle Databases with Transparent Data Encryption the DBA function does not have access to manage the keys, only to read and use them.
-	The Master key shall not be stored in any filesystem shared with the encrypted resource. Again, for using the Oracle Database with TDE as an example, the default key management with TDE is to use a Oracle Wallet stored in the same filesystem as the Oracle software installation. 
To meet these requirements and to have a robust operations model for key management, Oracle offers Oracle Key Vault.

Oracle key Vault offers two main categories of key management:  
   HSM based, with a FIPS compliant Hardware Security Module  
   Software Based, where the key is not stored in a HSM, but still protected with the strong tenant isolation and ops isolation that is the cornerstone of Oracle OCI.  

The main difference between HSM based Vaults and Software based is that the HSM based prohibits explicit export of the master key. HSM based key storage offers HA and DR, including cross region replication, slightly dependent of the type of HSM service deployed.

Software based Key Vault do not offer cross region replication.  
The main purpose of this asset is to provide an example python script that demonstrates usage of the Python KMS SDK, an example of OCI Vault software key backup/restore between two regions.  

## Prerequisites

- The script may be run from the Cloud Shell, or from a linux/Windows environment
- Python 3.0
- Create a virtual environment

```
[user]$ python -m venv ocienv
[user]$ source ocienv/bin/activate
```
- Install Oracle OCI CLI, if not run off Cloud Shell
  
Please refer to the OCI install guide.
  
[CLI Installation Guide](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/cliconcepts.htm)

  
- Install Python SDK into your virtual environment

```
[user]$ pip install oci
```

- Configure OCI profiles and verify the OCI SDK
Configure the OCI CLI with a API key (may be the same) for source and target. Please refer to the OCI CLI documentation for creating a OCI environment file. 

  
[OCI File Configuration]( https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliconfigure.htm)

  
The OCI CLI configuration may be verified with the following command:

```
[user]$ oci os ns get --profile myprofile
{
  "data": "<your namespace>"
}
```

- A valid public key for export only

- Create and/or Check IAM Policies to permit key read, inspect and key creation. 

Permission to `manage` the following types of resources in your Oracle Cloud Infrastructure tenancy: `vaults`, `keys`, `secret-family` 
Example policies:
```
Allow group SecurityAdmins to manage vaults in tenancy

Allow group SecurityAdmins to manage keys in tenancy

Allow group SecurityAdmins to manage secret-family in tenancy
```
[Policy Reference, Vault](https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm#sec-admins-manage-vaults-keys)


If you don't have the required permissions and quota, contact your tenancy administrator. See [Policy Reference](https://docs.cloud.oracle.com/en-us/iaas/Content/Identity/Reference/policyreference.htm), [Service Limits](https://docs.cloud.oracle.com/en-us/iaas/Content/General/Concepts/servicelimits.htm), [Compartment Quotas](https://docs.cloud.oracle.com/iaas/Content/General/Concepts/resourcequotas.htm).

## Script execution

The script requires a number of arguments. The arguments vary dependent on modi of script execution. All or some arguments can be submitted as a configuration file in JSON format or at the command-line. Any command-line argument overwrites any arguments from the configuration file,

The script has two modes of operation:
1)	Export a key, save it to a file, and print the fingerprint, used for verification of a key
2)	Copy the key between two locations where tenant OCID, region and API Key is required.

A key in vault may have several versions, and you may specify the OCID of a given version for both export and copy of the key. If no key version is specified, the most recent key is exported.

The script checks if the key is Enabled and is of type SOFTWARE, before any export is attempted.

##  Configuration parameters/arguments

ociconfig path to OCI configuration file  
source_ociprofile Source profile in oci config  
source_region Source Region  
source_compartment Source Compartment  
source_vault Source vault OCI  
source_keyname Source Key Name, if search for key  
source_key_ocid Source key OCID if search for OCID  
source_key_version OCID of a specific key version, if not set pick latest version  
  
target_region Target Region  
target_compartment Target Compartment  
target_vault Target Vault OCID  
target_ociprofile Target profile in oci config  
target_keyname Target keyname, the copy will be created with this name  
  
exportonly only save to file or print  key, don't backup  
wrapping_pubkey_file If it supplied filepointer  external key for wrapping  
outputfile File for the exported key  

## Example execution
Example export
```
python kms_key_backup.py --configfile kms_backup.json --target_keyname test1 --source_key_ocid ocid1.key.oc1.eu-frankfurt-1.xxxxxx --exportonly --wrapping_pubkey_file export_pub.pem --source_key_version ocid1.keyversion.oc1.eu-frankfurt-1.qwertyqwerty
```
with configfile:
```
{
    "ociconfig":"/home/myhome/.oci/config",
    "source_ociprofile":"my-config-fra",
    "source_region" : "eu-frankfurt-1",
    "source_compartment" : "ocid1.compartment.oc1..aaaaaaaa",
    "source_vault" : "ocid1.vault.oc1.eu-frankfurt-1.aaaeeeqqqlllaleaeqlr",
    "wrapping_algorithm" :  "RSA_OAEP_AES_SHA256"
}
```
Example backup
```
python kms_key_backup.py --configfile kms_backup.json --target_keyname test2 --source_key_ocid ocid1.key.oc1.eu-frankfurt-1.eeeeaaaaaaa  --source_key_version ocid1.keyversion.oc1.eu-frankfurt-1.qfqfqfqfqfaeaea
```
with configfile:
```
{
    "ociconfig":"/home/myhome/.oci/config",
    "source_ociprofile":"my-config-fra",
    "source_region" : "eu-frankfurt-1",
    "source_compartment" : "ocid1.compartment.oc1..aaaaaaaa",
    "source_vault" : "ocid1.vault.oc1.eu-frankfurt-1.aaaeeeqqqlllaleaeqlr",
    "source_key_ocid" : "ocid1.key.oc1.eu-frankfurt-1.sxesxesxesxe",
    "target_region" : "eu-stockholm-1",
    "target_compartment" : "ocid1.compartment.oc1..aaaaaaaa",
    "target_vault" : "ocid1.vault.oc1.eu-stockholm-1.qewuroewrre",
    "target_ociprofile":"my-config-ams",
    "wrapping_algorithm" :  "RSA_OAEP_AES_SHA256"
}
```




# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.


