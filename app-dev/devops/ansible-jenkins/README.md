# ansible-jenkins

## Getting started

This Terraform code provisions a new OCI instance and installs Jenkins directly through an Ansible playbook.
To optimize and be more cost-efficient, the instance shape is locked to VM.Standard.A1.Flex, but this code
can eventually be modified or forked.

## Features and limitations
* Get quickly started with the latest Jenkins version on OCI
* Manage plugins and the installation through Ansible and Jenkins Configuration as Code
* Tested on Oracle Linux 8
* Instance generated only if it is in a public subnet network
* Port 22 must be opened on the instance, as OCI Resource Manager will need to connect to the instance through SSH

Although these limitations might not fit every use case, the code can be used as a reference and there are ways to lift them.

