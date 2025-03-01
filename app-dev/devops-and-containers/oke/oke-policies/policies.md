## OKE Policies

  

### VCN NATIVE CNI

When network compartment is not the same as OKE compartment AND OKE is using VCN\_NATIVE CNI

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpodnetworking\_topic-OCI\_CNI\_plugin.htm](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpodnetworking_topic-OCI_CNI_plugin.htm)  

```
Allow any-user to manage instances in compartment <compartment-ocid-of-nodepool> where all { request.principal.id = '<cluster-ocid>' }
Allow any-user to use private-ips in compartment <compartment-ocid-of-network-resources> where all { request.principal.id = '<cluster-ocid>' }
Allow any-user to use network-security-groups in compartment <compartment-ocid-of-network-resources> where all { request.principal.id = '<cluster-ocid>' }
```

  

### USE IPv6 WITH VCN NATIVE CNI

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpodnetworking\_topic-OCI\_CNI\_plugin.htm](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpodnetworking_topic-OCI_CNI_plugin.htm)  

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/conteng\_ipv4-and-ipv6.htm](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/conteng_ipv4-and-ipv6.htm)  

UNCLEAR: Maybe this policy is necessary for every IPv6 cluster

```
Allow any-user to use ipv6s in compartment <compartment-ocid-of-network-resources> where all { request.principal.id = '<cluster-ocid>' }
```

  

### ENCRYPT BOOT VOLUME WITH KEY

To encrypt OKE worker nodes boot volume with a key that is in a different compartment than the worker nodes

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig\_topic\_Create\_Policies\_for\_User\_Managed\_Encryption](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig_topic_Create_Policies_for_User_Managed_Encryption)  

```
Allow any-user to use key-delegates in <compartment-key> where ALL {request.principal.type='nodepool', target.key.id = '<key_OCID>'}
Allow service blockstorage to use keys in compartment <compartment-key> where target.key.id = '<key_OCID>'
Allow any-user to use key-delegates in compartment <compartment-key> where ALL {request.principal.type='nodepool', target.key.id = '<key_OCID>'}
```

  

### ENCRYPT BLOCK VOLUME WITH KEY

To enable encryption on block volumes with a key in a different compartment than the worker nodes

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig\_topic\_Create\_Policies\_for\_User\_Managed\_Encryption](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig_topic_Create_Policies_for_User_Managed_Encryption)  

```
Allow service blockstorage to use keys in compartment <compartment-key> where target.key.id = '<key-ocid>'
Allow any-user to use key-delegates in compartment <compartment-key> where ALL {request.principal.type = 'cluster', target.key.id = '<key-ocid>'}
```

  

### ENCRYPT FILE SYSTEM

To enable in-transit/in-place encryption of FSS

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig\_topic\_Create\_Policies\_for\_User\_Managed\_Encryption](https://docs.oracle.com/en-us/iaas/Content/ContEng/Concepts/contengpolicyconfig.htm#contengpolicyconfig_topic_Create_Policies_for_User_Managed_Encryption)  

```
Dynamic Group
ALL { resource.type='filesystem', resource.compartment.id = '<file_system_compartment_OCID>' }

Allow dynamic-group <domain>/<dynamic-group-name> to use keys in compartment <key-compartment-name>
Allow any-user to use key-delegates in compartment <compartment-key> where ALL {request.principal.type = 'cluster', target.key.id = '<key_OCID>'}
```

  

### ENABLE CCM TO MANAGE NSGs FOR LBs and NLBs

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer\_topic-Specifying\_Load\_Balancer\_Security\_Rule\_Management\_Annotation](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer_topic-Specifying_Load_Balancer_Security_Rule_Management_Annotation)

```
ALLOW any-user to manage network-security-groups in compartment <compartment-name> where request.principal.type = 'cluster'
ALLOW any-user to manage vcns in compartment <compartment-name> where request.principal.type = 'cluster'
ALLOW any-user to manage virtual-network-family in compartment <compartment-name> where request.principal.type = 'cluster'
```

  

### TAGGING RESOURCES DIFFERENT COMPARTMENT

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengtaggingclusterresources\_iam-tag-namespace-policy.htm#contengtaggingclusterresources\_iam-tag-namespace-policy](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengtaggingclusterresources_iam-tag-namespace-policy.htm#contengtaggingclusterresources_iam-tag-namespace-policy)

```
Allow any-user to use tag-namespace in compartment <compartment-ocid-tag-namespace> where all { request.principal.id = '<cluster-ocid>' }
```

  

### USE MANAGED NODE POOL WITH CAPACITY RESERVATION

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengmakingcapacityreservations.htm#contengmakingcapacityreservations\_topic\_Using\_capacity\_reservations](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengmakingcapacityreservations.htm#contengmakingcapacityreservations_topic_Using_capacity_reservations)  

```
Allow service oke to use compute-capacity-reservations in compartment id <compartment_capacity>
Allow any-user to use compute-capacity-reservations in tenancy where request.principal.type = 'nodepool'
```

  

### USE RESERVED PUBLIC IP IN DIFFERENT COMPARTMENTS THAN OKE

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer\_topic\_Specifying\_Load\_Balancer\_Reserved\_IP](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer_topic_Specifying_Load_Balancer_Reserved_IP)  

If it is a LB:

```
ALLOW any-user to read public-ips in tenancy where request.principal.type = 'cluster'
ALLOW any-user to manage floating-ips in tenancy where request.principal.type = 'cluster'
```

  

If it is a NLB:

```
ALLOW any-user to use private-ips in TENANCY where ALL {request.principal.type = 'cluster', request.principal.compartment.id = 'target.compartment.id'}
ALLOW any-user to manage public-ips in TENANCY where ALL {request.principal.type = 'cluster', request.principal.compartment.id = 'target.compartment.id'}
```

  

### ATTACH NSGs WHEN THEY ARE IN DIFFERENT COMPARTMENTS THAN OKE

[https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer\_topic\_Specifying\_Load\_Balancer\_Network\_Security\_Group](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contengconfiguringloadbalancersnetworkloadbalancers-subtopic.htm#contengcreatingloadbalancer_topic_Specifying_Load_Balancer_Network_Security_Group)  

```
Allow any-user to use network-security-groups in compartment <network-compartment-ocid> where all { request.principal.id = '<cluster-ocid>' }
```