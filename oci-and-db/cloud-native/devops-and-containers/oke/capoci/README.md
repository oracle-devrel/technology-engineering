# CAPOCI

Reviewed: 07.09.2026

# When to use this asset?
 
# How to use this asset?

## CAPOCI installation
This project includes a simplified procedure to deploy and use Cluster API inside any
OKE cluster.
The only prerequisite is to have an Oracle Cloud tenancy with an OKE cluster already
provisioned and accessible.

1. Create a dynamic group for the OKE cluster. As an example, we will call the
dynamic group my-oke-cluster:  
` instance.compartment.id = 'OKE_COMPARTMENT_ID' `
2. Create the following policies:
    ``` 
        Allow dynamic-group <oke-dynamic-group> to manage instance-family in compartment <compartment name>
        Allow dynamic-group <oke-dynamic-group> to manage virtual-network-family in compartment <compartment name>
        Allow dynamic-group <oke-dynamic-group> to manage cluster-family in compartment <compartment name>
    ```
3. Open the Cloud Shell, upload the install.sh script and execute it. Be sure that your
Kubeconfig file is correctly configured and in the right context.
4. To provision another OKE cluster, substitute the variable in oke-capoci.yaml and
apply it to the cluster.
5. See the creation of the OKE cluster and the Node Pool.

NOTE: The cluster deployed here is very simple, but you can actually configure it in
every aspect, you can configure the network and even create Virtual Node clusters!

# License

Copyright (c) 2026 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.