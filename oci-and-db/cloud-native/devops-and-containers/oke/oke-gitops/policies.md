Dynamic group needed:

```
DevOpsDynamicGroup
NOTE: CompartmentOCID == compartment id where the OCI DevOps is located

ALL {resource.type = 'devopsdeploypipeline', resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsrepository', resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsbuildpipeline',resource.compartment.id = 'compartmentOCID'}
ALL {resource.type = 'devopsconnection',resource.compartment.id = 'compartmentOCID'}

```

Policies needed:
```
NOTE1: CompartmentOCID == compartment id where the OCI DevOps is located
NOTE2: CompartmentOCIDNetwork == compartment id where the network for the OKE cluster has been provisioned
NOTE3: CompartmentOCIDOKE == compartment id where the OKE cluster is provisioned

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage repos in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage devops-family in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use ons-topics in compartment id compartmentOCID

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use subnets in compartment id compartmentOCIDNetwork
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use vnics in compartment id compartmentOCIDNetwork
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to use network-security-groups in compartment id compartmentOCIDNetwork

Allow dynamic-group <domain-name>/DevOpsDynamicGroup to read all-artifacts in compartment id compartmentOCID
Allow dynamic-group <domain-name>/DevOpsDynamicGroup to manage cluster in compartment id compartmentOCIDOKE
```