# Importing keys into OCI KMS Vaults

Owner: Leon van Birgelen

Key Management Service is an OCI service that stores and manages keys for secure access to resources.

The Oracle Cloud Infrastructure (OCI) [Key Management Service](https://oracle.com/security/cloud-security/key-management/) (KMS) is a cloud-based service that provides centralized management and control of encryption keys for data stored in OCI.

One of the capabilities of OCI KMS is to import Vault Keys and Key Versions, in case you want to "bring your own key" (BYOK). There is [detailed documentation](https://docs.public.oneportal.content.oci.oraclecloud.com/en-us/iaas/Content/KeyManagement/Tasks/importingkeys.htm) available on this process but in this example below you will find a brief guide on how to this as it is a tedious and detailed process.

This example is for a RSA 2048 Asynchronous key to be imported.

# Prerequisites

- Make sure to have a up-to-date version of OpenSSL installed that supports the RSA_OAEP_AES_SHA256 wrapping mechanism. OCI CloudShell is currently based on Oracle Linux 7, which does not have the minimum required version of OpenSSL installed.

- Get a RSA 2048 Key Pair to import and store in the file name **my_keypair.pem**, or generate one via this command:

  ```openssl genrsa -out my_keypair.pem 2048```

# Create the wrapped key material to be imported

1. Create an OCI Vault and copy the Public Wrapping Key. You can find it when creating a new Key in the Vault and enabling the "Import External key" checkbox. For this example store the wrapping key in file called **pub_wrapping_key.pem**

2. Create a temporary AES key:

   ```openssl rand -out temp_aes.key 32```

3. Wrap the temporary AES Key:

   ```openssl pkeyutl -encrypt -in  temp_aes.key -inkey pub_wrapping_key.pem -pubin -out wrapped_temp_aes.key -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256```

4. Create a hexdump of the temporary AES key:

   ```export temporary_AES_key_hexdump=$(hexdump -v -e '/1 "%02x"' < temp_aes.key)```

5. Extract the private key from the to be imported RSA key:

   ```openssl pkcs8 -topk8 -nocrypt -inform PEM -outform DER -in my_keypair.pem -out my_private_key.key```

6. Encrypt the private key with the temporary AES key:

   ```openssl enc -id-aes256-wrap-pad -iv A65959A6 -K $temporary_AES_key_hexdump -in my_private_key.key -out my_wrapped.key```

7. Concatenate the wrapped temporary AES key with the wrapped private key into the to be imported key material:

   ```cat wrapped_temp_aes.key my_wrapped.key > wrapped_key_material.key```

# Import the wrapped key material

- From the OCI Vault where the Public Wrapping Key was retrieved, create a Key and select the RSA as Key Shape Algorithm with the length 2048.
- Have hte Import External key checkbox enabled.
- The Wrapping Algorithm should be automatically set to "RSA_OAEP_AES_SHA256"
- Upload the wrapped key material file **wrapped_key_material.key**
- Click on the Create Key button.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
