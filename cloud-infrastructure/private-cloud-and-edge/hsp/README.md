# C3 Hosting Service Provider - IAM Policies for Isolation

The Hosting Service Provider (HSP) model on C3 allows hosting for a
maximum of 8 end customers, each isolated in a dedicated compartment
with a single VCN per customer. To ensure the end customer can only
create resources in just their own compartment a set of IAM policies are
required.

The HSP documentation suggests the following policies per end customer
based on an example with two hosting customers, A & B. They assume that
each end customer will have two roles for their
staff: Customer Administrator and Customer End User. 

## Example Policies for Customer Administrator
```
Allows the group specified to use all C3 services in the compartment
listed:

Allow group CustA-Admin-grp to manage all-resources in compartment
path:to:CustA

Allow group CustB-Admin-grp to manage all-resources in compartment
path:to:CustB
```
Note that the above policy grants permissions in the CustA and CustB
compartments of the C3 but **also in the same compartment in the OCI
tenancy**! To prevent permissions being granted in the OCI tenancy
append a condition such as:

```Allow group CustA-Admin-grp to manage all-resources in compartment
path:to:CustA where all {request.region != 'LHR',request.region !=
'FRA'}

Allow group CustB-Admin-grp to manage all-resources in compartment
path:to:CustB where all {request.region != 'LHR',request.region !=
'FRA'}
```
In the example above the condition prevents resource creation in London
and Frankfurt regions. Adjust the list to include all regions the
tenancy is subscribed to.

The path to the end user compartment must be explicitly stated, using
the comma format, relative to the compartment where the policy is
created. 

## Example Policies for Customer End User
```
Allow group CustA-Users-grp to manage instance-family in compartment
path:to:CustA  
Allow group CustA-Users-grp to use volume-family in compartment
path:to:CustA  
Allow group CustA-Users-grp to use virtual-network-family in compartment
path:to:CustA  
Allow group CustB-Users-grp to manage instance-family in compartment
path:to:CustB  
Allow group CustB-Users-grp to use volume-family in compartment
path:to:CustB  
Allow group CustB-Users-grp to use virtual-network-family in compartment
path:to:CustB
```
As above append a condition to limit permissions to the C3 and prevent
resource creation in OCI regions:
```
Allow group CustA-Users-grp to manage instance-family in compartment
path:to:CustA where all {request.region != 'LHR',request.region !=
'FRA'}  
Allow group CustA-Users-grp to use volume-family in compartment
path:to:CustA where all {request.region != 'LHR',request.region !=
'FRA'}  
Allow group CustA-Users-grp to use virtual-network-family in compartment
path:to:CustA where all {request.region != 'LHR',request.region !=
'FRA'}  
Allow group CustB-Users-grp to manage instance-family in compartment
path:to:CustB where all {request.region != 'LHR',request.region !=
'FRA'}  
Allow group CustB-Users-grp to use volume-family in compartment
path:to:CustB where all {request.region != 'LHR',request.region !=
'FRA'}  
Allow group CustB-Users-grp to use virtual-network-family in compartment
path:to:CustB where all {request.region != 'LHR',request.region !=
'FRA'}
```
## Common Policy

Currently any user of a C3 needs access to certain resources located at
the tenancy level to use IaaS resources withgout errors in the web UI.
Backup policies, tag namespaces, platform images all reside at the
tenancy level and need a further policy to allow normal use of C3 IaaS
services. Note that this is **different** to the behaviour on OCI. 

An extra policy as below is required (where CommonGroup contains **all**
HSP users on the C3):
```
allow group CommonGroup to read all-resources in tenancy where
target.compartment.name='root-compartment-name'
```

