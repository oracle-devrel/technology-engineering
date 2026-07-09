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
* Jenkins port can't be between 0 and 1024, as those are Linux reserved ports and would require further configurations to be exposed
* To access Jenkins, the instance and Jenkins port must be reachable
* As the instance will be updated, it will take a while during the first run

Although these limitations might not fit every use case, the code can be used as a reference and there are ways to lift them.

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/technology-engineering/raw/main/app-dev/devops-and-containers/devops/ansible-jenkins/ansible-jenkins-rm.zip)

