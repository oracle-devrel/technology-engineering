# Importing keys into OCI KMS Vaults

Owner: Leon van Birgelen

Key Management Service is an OCI service that stores and manages keys for secure access to resources.

The Oracle Cloud Infrastructure (OCI) [Key Management Service](https://oracle.com/security/cloud-security/key-management/) (KMS) is a cloud-based service that provides centralized management and control of encryption keys for data stored in OCI.

One of the capabilities of OCI KMS is to import Vault Keys and Key Versions, in case you want to "bring your own key" (BYOK). There is [detailed documentation](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/KeyManagement/Tasks/importingkeys.htm) available on this process but in this example below you will find a brief guide on how to this as it is a tedious and detailed process.


# Importing a RSA 2048 Asynchronous key

This example is for an RSA 2048 Asynchronous Key to be imported in OCI Vault. There are also examples for Synchronous Keys and for importing key versions, see the documentation as mentioned above.

## Prerequisites

- Make sure to have a up-to-date version of OpenSSL installed that supports the RSA_OAEP_AES_SHA256 wrapping mechanism. OCI CloudShell is currently based on Oracle Linux 7, which does not have the minimum required version of OpenSSL installed. If you create an OCI Compute based on Oracle Linux 9, it should work immediately.

- Get a RSA 2048 Key Pair to import and store in the file name ```my_keypair.pem```, or generate one via this command:

  ```openssl genrsa -out my_keypair.pem 2048```

- Create an OCI Vault and copy the Public Wrapping Key. You can find it when creating a new Key in the Vault and enabling the "Import External key" checkbox. For this example store the wrapping key in file called ```pub_wrapping_key.pem```

### Manually create the wrapped key material to be imported

1. Create a temporary AES key:

   ```openssl rand -out temp_aes.key 32```

2. Wrap the temporary AES key with the public wrapping key using RSA-OAEP with SHA-256:

   ```openssl pkeyutl -encrypt -in  temp_aes.key -inkey pub_wrapping_key.pem -pubin -out wrapped_temp_aes.key -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256```

3. Generate hexadecimal of the temporary AES key material:

   ```export temporary_AES_key_hexdump=$(hexdump -v -e '/1 "%02x"' < temp_aes.key)```

4. If the RSA private key you want to import is in PEM format, convert it to DER:

   ```openssl pkcs8 -topk8 -nocrypt -inform PEM -outform DER -in my_keypair.pem -out my_private_key.key```

5. Wrap your RSA private key with the temporary AES key:

   ```openssl enc -id-aes256-wrap-pad -iv A65959A6 -K $temporary_AES_key_hexdump -in my_private_key.key -out my_wrapped.key```

6. Create the wrapped key material by concatenating both wrapped keys:

   ```cat wrapped_temp_aes.key my_wrapped.key > wrapped_key_material.key```

### Use the provided script to generate the wrapped key material to be imported

The script is provided in the OCI Documentation [here](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/KeyManagement/Tasks/importing_asymmetric_keys_topic_script_to_import_rsa_key_material_as_a_new_external_key.htm)

Just copy the script and place it on an environment where you have the correct version of openssl (see pre-requisites). Then modify the script to have the correct values to point to the required input files. The below example shows how to set the values when you use an OCI Compute with Oracle Linux 9:

```
OPENSSL_PATH="/usr/bin/openssl"
PRIVATE_KEY="my_keypair.pem"
WRAPPING_KEY="pub_wrapping_key.pem"
```

After the script has run, the wrapped key material files are available in a tmp folder as listed on screen and can be used to import the key as mentioned in the next step.

If you want to automate the import to OCI as well, the script has already some example code in it that can be used as a starting point for this. Just also make sure that you setup OCI Permissions and grant these to the compute's instance principles via a dynamic group. See the OCI Documentation for more details on permissions [here](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/KeyManagement/Tasks/importingkeys.htm#permissions).

## Import the wrapped key material

- In the OCI Console from the OCI Vault where the Public Wrapping Key was retrieved, click Create a Key and select the RSA as Key Shape Algorithm with the length 2048.
- Have the Import External key checkbox enabled.
- The Wrapping Algorithm should be automatically set to "RSA_OAEP_AES_SHA256"
- Upload the wrapped key material file ```wrapped_key_material.key```
- Click on the Create Key button.
- Make sure to cleanup the used files as private keys should never be left somewhere on a filesystem.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
