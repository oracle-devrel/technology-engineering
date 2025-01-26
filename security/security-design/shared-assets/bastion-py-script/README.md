
# Oracle Cloud Infrastructure (OCI) Bastion Service

This reusable asset consist of a Python script that creates a bastion session with the Oracle OCI Bastion Service.  The main purposes of this asset are:  

-	Demonstrate the usage of OCI Python SDK
-	Create a simple OS independent command-line interface for creating bastion sessions
-	Create a simple way to make reusable configuration
-	Create a `ssh` command that works with Linux, Mac OS and Windows by providing the flexibility to configure either `ssh` command or `putty` commands.  

The script creates bastion session over SSH, and creates an example command to set up the tunnel for the target application. Other protocols like RDP can then be tunneled over the SSH session through the OCI Bastion Service.  

Some documentation for inspiraton:

[https://www.ateam-oracle.com/post/openssh-proxyjump-with-oci-bastion-service](https://www.ateam-oracle.com/post/openssh-proxyjump-with-oci-bastion-service)  
[https://fluffyclouds.blog/2022/06/02/create-oci-bastion-sessions-with-python-sdk/](https://fluffyclouds.blog/2022/06/02/create-oci-bastion-sessions-with-python-sdk/)

## Why use the OCI Bastion Service

Oracle Cloud Infrastructure (OCI) Bastion Service, is a fully managed service providing secure and ephemeral Secure Shell (ssh) access to the private resources in OCI. OCI Bastion Service, like the bastion fortress of medieval times, improves security posture by providing an additional layer of defense against external threats.    

Accessing virtual services directly from the internet is a clear no-go. Best practices is to never expose compute resources directly, neither for SSH or RDP traffic. RDP is known to be one of the most common Initial Access Vectors for ransomware types of attacks.  

Common practice is to place a compute node with a minimum OS in a DMZ as jump host, and always use this as the entrypoint.  
The main weakness with this model is:
-	A extra computer-node that needs to be managed, monitored and patched
-	Extra set of required resources with risk of misconfiguration
-	The jump server will require an additional layer of user governance.
  
The OCI Bastion Service removes the public and private virtual cloud networking (VCN) hassle for access to a jump host. No public IP is needed, resulting in no surface attack area or zero-day vulnerabilities with a dedicated jump host. Customers also eliminate shared credentials, broad access limits, and other bad habits of using jump hosts. OCI Bastion Service integrates with OCI Identity and Access Management (IAM) and allows the organization to control who can access a bastion or a session and what they can do with those resources.
  
The OCI Bastion Service exists in two flavors:
-	Managed Session
With managed sessions an agent is running on the compute node, and the bastion session connects to the agent and tunnels SSH through the agent. The managed session makes it possible to connect to a compute node from other networks without configure routing between the network where the compute node resides, and the network the bastion connection is initiated from.
-	Port Forwarding
In this mode the OCI Bastion Service does not tunnel though the agent, but the OCI Bastion Service must have access to the subnet where the compute node resides, and the subnet security list
For additional description of the OCI Bastion Service please review:

## Requirements  

The following components needs to be installed in your environment:
- python 3.8 or above (latest patch version)  
- Latest version of the OCI CLI 
- Requirements, as defined in requirements.txt

If you need to run older Python versions (below 3.8), note the changes for asyncio in the exec_command procedure.  

[OCI CLI Install guide](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/cliinstall.htm)

The file requirements.txt lists the Python modules required.
Install the required modules with 

```pip install -r requirements.txt```  

  
## Script Usage  

In addition, the script require a JSON configuration file. 

The basic structure of the config file looks like:  
```
{ "sessions":[  
                { <session one points to ociconfigurations>},  
                { <session two points to ociconfigurations>}],  
  "ociconfigurations": [  
                { <ociconfiguration one>},  
                { <ociconfiguration one>}]  
}  
```
For example, review [config_example.json](files/config_example.json)  

The following elements exists in the configuration file.  

- "sessions":  JSON array with one JSON config entry pr. Session
- "ociconfigurations": JSON Array with one JSON element pr. OCI SDK configuration profile.
  
Each “session” element has the following elements:
- "sessionType":"PORT_FORWARDING" or MANAGED
- "OCIConfig"-: name of profile, it looked up in the ociconfigurations array 
- "bastionOCID": OCID to the configured OCI Bastion service 
- "bastionPublicKeyFile":file with public key to the Bastion SSH session
- "bastionPrivateKeyFile":Private key of bastion session key pair,
- "targetPrivateKeyFile":Used for reference in the target `ssh` command,
- "targetPort": Portnumber for the target SSH tunnel though the bastions Service. Use standard port for RDP if target is RDP,
- "localPort":"2222",
- "sessionDisplayName": Display name of the session in the OCI Console
- "targetOCIDID":OCID of the target service,
- "targetPrivateIP":IP Address of the target
- "osUserName": Used for the generated `ssh` command ,
- "ociRegion": Region where the target resource runs,
- "timetolive":Time the Bastion tunnel lives. Maximum value is 3600 sec.,
- "maxWaitCount":If the script creates the tunnel after creation of the session, maximum number of retries
- "waitRefresh": time in sec, between each retry to establish the tunnel
- "ociconfigurations": Array of OCI configurations  

Each array entry got the following JSON elements
- "configName": Name of entry. Referenced from a session element above
- "configFileName": Path to the OCI CLI configuration file
- "profileName": Name of profile in the OCI CLI configuration file
      

```Script commandline options.
 --configfile  name of JSON configfile with named session and OCI CLI config info
 --session     named session, section in config file
 --exec        executes the `ssh` command and establishes the SSH connection
 --loglevel    logging level, info or debug. default info
 --log         logging output file or stdout, defaul stdout
```
Example command:  

Example commandline:  
```python bastionsession.py --session port-example --configfile config_examlpe.json --loglevel debug```  

Sample output

```
Bastion session manager 1.0 17.11.24

INFO:root:Open logfile
Open logfile: stderr
Successfully loaded session and OCI Config parameters
Waiting for session state to be active. Current State ..CREATING
Session has been created and is ACTIVE
Bastion session created
Port managed start cmd
Port forwarding start cmd
ssh -i <privateKey> -N -L <localPort>:10.10.1.229:22 -p 22 ocid1.bastionsession.oc1.eu-frankfurt-1.ama...ama@host.bastion.eu-frankfurt-1.oci.oraclecloud.com
ssh tunnel command:
putty -i c:\\usr\\ssh_keys\\mykey.ppk -N -ssh -L 2222:10.10.1.229:22  ocid1.bastionsession.oc1.eu-frankfurt-1.ama...ama@host.bastion.eu-frankfurt-1.oci.oraclecloud.com
Client Connect:
putty -i c:\\usr\\ssh_keys\\myprivatetkey.ppk -P 2222 ios@localhost
Successfully completed bastion session(s)
```
  
# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.