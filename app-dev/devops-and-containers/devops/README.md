# DevOps
 
OCI DevOps, OCI Resource Manager, Visual Builder Studio, Open Source tools

Reviewed: 08.05.2024
 
# Team Publications

- [Deploying Jenkins on Oracle Container Engine for Kubernetes](https://docs.oracle.com/en/solutions/oci-jenkins-oke/index.html#GUID-23A8EB94-DFFC-4D5C-897F-5F59423447D2)
 

# Useful Links

- [A DevOps Engineer's guide to OCI](https://docs.oracle.com/en-us/iaas/Content/GSG/Reference/getting-started-as-devops.htm)
- [Selecting an appropriate CI/CD architecture](https://docs.oracle.com/en/solutions/select-cicd-architecture/index.html#GUID-A7048F76-5D10-4541-A105-CCF1CEFABEE1)

## OCI DevOps

- [OCI DevOps Build Pipeline collection](https://github.com/oracle-devrel/oci-devops-examples)
- [OCI CLI documentation](https://docs.oracle.com/iaas/tools/oci-cli/latest/oci_cli_docs/)
- [Deploying a Helm chart with Provenance liveLab](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3664&clear=RR,180&session=109957900717640)
- [Sample build-spec.yaml](./devops-graalvm-native-image/build-spec.yaml) and [associated Dockerfile](./devops-graalvm-native-image/Dockerfile) to use with OCI Devops. These are very configurable and show the installing of specific versions of software (GraalVM and Maven) into the build environment, creating of a native image executable using the installed software, determining version information dynamically and creating a docker image. The example used is the Quarkus getting-started example, but the build command should be the same for all quarkus examples, for Helidon and others you may need to change it slightly. This also assumes that the projects code base is in a sub directory of the gir repo (callsed getting-started in this case) you will need to modify the PROJECT_PATH_TO_BUILD to reflect a different location. To use this in a devops build pipeline place the Dockerfile and build-spec.yml in your projects code root (where the pom.xml file is). Adjust the PROJECT_PATH_TO_BUILD in the build spec and other variables as needed, add the files to your git repo. Change the output stage names for the image if needed. Configure the git repo as the primary GIT repo for the projects build stage and specify the build-spec.yaml file location.

## Terraform

- [OCI Terraform provider](https://registry.terraform.io/providers/oracle/oci/latest/docs)
- [Oracle quick start - automated deployments](https://github.com/oracle-quickstart)

## Ansible

- [Getting starter - Ansible with OCI](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/ansiblegetstarted.htm#Getting_Started_with_Oracle_Cloud_Infrastructure_and_Ansible)
- [OCI Ansible Collection documentation](https://docs.oracle.com/en-us/iaas/tools/oci-ansible-collection/latest)
- [Using Ansible Playbooks](https://docs.ansible.com/ansible/latest/playbook_guide/index.html)
- [Ansible builtin modules](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/index.html)
- [Oracle Linux Automation Manager](https://docs.oracle.com/en/operating-systems/oracle-linux-automation-manager/index.html)
 
# License
 
Copyright (c) 2024 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/application-development/cloud-native/approach-workshop/LICENSE) for more details.
