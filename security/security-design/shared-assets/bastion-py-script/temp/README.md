# Bastion session
Python script to create an OCI bastion session from script
Make life simple, you do not need to go through the UI to get an keep a valid bastion session

Script to create a session for a named bastion services, and generates the ssh command for connection to the session
Python version: 3.8 or above

The Session have two formats:
 - Just print the commands
 - Fork a bash shell and run the commands. In the latter case it waits for the session to expire and recreates a new, x number of times
for PORT type SSH session, start a ssh tunnel, for managed session, connect to the target

 Command line:
 --configfile  name of json configfile with named session and OCI CLI config info  
 --session     named session, section in config file  
 --printonly   Y|TRUE|N|FALSE  if TRUE or Y, only print ssh commands to connect upon successfull creation  
               if FALSE or N, forks bash shell with ssh command, not valid if session type == managed  
--loglevel     logging level, info or debug. default info  
--log          logging output file or stdout, defaul stdout  


  
  If File location is missing, the default config will be used. If profile_name is missing DEFAULt fill be used
  If the OCIconfigname parameter is missing in the session section, DEFAULT from DEFAULT location will be used.

Documentation for inspiraton:

[https://www.ateam-oracle.com/post/openssh-proxyjump-with-oci-bastion-service](https://www.ateam-oracle.com/post/openssh-proxyjump-with-oci-bastion-service)  
[https://fluffyclouds.blog/2022/06/02/create-oci-bastion-sessions-with-python-sdk/](https://fluffyclouds.blog/2022/06/02/create-oci-bastion-sessions-with-python-sdk/)

The basic structure of the config file:  
```
{ "sessions":[  
                { <session one points to ociconfigurations>},  
                { <session two points to ociconfigurations>}],  
  "ociconfigurations": [  
                { <ociconfiguration one>},  
                { <ociconfiguration one>}]  
}  
```
For example, reviev config_example.json

Example commandline:  
```python bastionsession.py --session port-example --configfile config_examlpe.json --printonly False --loglevel debug```
