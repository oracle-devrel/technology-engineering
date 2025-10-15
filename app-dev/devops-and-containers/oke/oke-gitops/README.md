# OKE GitOps with ArgoCD

This repository's objective is to get you started quickly adopting a GitOps strategy for managing your OKE cluster.
GitOps is just a series of best practices to manage operation using a Git repository.
Administering a Kubernetes cluster is not an easy task, and I often see people getting lost in the forest of YAMLs and, with time,
losing track of what is actually deployed in the cluster.

To help simplifying the experience, it would be optimal to have all the configurations in a Git repository, so that we
can organize our YAMLs in folders and inspect the code when we forget some nuances abut what has been already deployed.

Problem is, GitOps requires a shift in mentality, as most of the operation team I have met are not familiar with Kubernetes, Git and modern operations.

Hence, the idea of creating this template to get people started with GitOps and ArgoCD to manage OKE clusters.

Before actually starting, it's good to remind us some best practices and concepts.

## WHY GitOps?

Traditionally, a Git repository is used by developers to version their custom application code.
With recent years, the types of things we can create through code has drastically spiked, so Git repositories are also used by operation teams.
Some examples:

* Application code
* Configuration as Code
* Infrastructure as Code

Having everything as code might seem something difficult and pointless at first, but with time, as the number of components increases, you will find out that it's way easier to debug complex and big
systems if you have them defined as code.

After all, the key to effectively manage a complex infrastructure is to have everything visible and do not lose control as complexity spikes.
Some other advantages of GitOps are:
* Faster and safer deployments
* Easier rollbacks
* Straightforward auditing
* Better traceability
* Eliminating configuration drift

## WHY Kubernetes?

When organizations start thinking of adopting Kubernetes as the reference development platform, I have always seen people struggling
to get used to it, especially the operation teams who were used to managing on-prem servers or VMs.
Some people even fear Kubernetes, saying it adds too much complexity in any architecture, and also that there is too much to study to get used to it.
Working with customers, I have heard many good and bad things about Kubernetes, but in my opinion the truth lies in between.
Let's see some common thinking I have observed over these years:
* Kubernetes is just another system we need to take care of.
  * A: no it is not! Kubernetes is a PLATFORM where other platforms are deployed on top of it. Think about it, in Kubernetes you can deploy anything: database systems, applications, Kafka, OpenSearch, caching systems and so on. Potentially, you could have your entire IT infrastructure deployed in a single Kubernetes cluster.
* Kubernetes is too complex to actually use it
  * A: it is indeed complex, as it is a very powerful platform, but once you get the hang of it, it will become eventually easy. Not everything can be easy at first, especially if we want to manage a platform to create other platforms.
  * A: There are also many tutorials and a rich documentation, as well as certifications and courses. But of course, the best way to learn is always through practice.
* Q: Why is Kubernetes so complex?
  * A: Kubernetes is an Open Source platform, where people are supposed to deploy applications and the tools they prefer.
    Being an open and customizable platform, there are a lot of choices to make and a lot of possibilities. If people are given
    a lot of options, they tend to get lost in this maze of choices, especially if it is the first time they are dealing with Kubernetes.
    For example, I often get these questions:
    * How can we secure our Kubernetes cluster?
    * Which ingress controller should we use? Or is it better to use Gateway API?
    * Which tools are we supposed to use for logging? And what about monitoring and tracing?
    * How many Kubernetes clusters should we have?
    * How can we manage certificates?
    * Should we have a service mesh in place?
  * As a general suggestion, freedom of choice shouldn't be seen as something overwhelming, but it should be regarded as something positive.
    You can start by deploying a tool based on some suggestions, evaluate it and uninstall it from the cluster if you don't like it.
* Q: What is the main challenge of managing a Kubernetes cluster?
  * A: In my opinion, what I have seen is that people struggle to administer a cluster because of lack of experience, automations and standards.
    Because of deadlines and other priorities, it is also difficult for people in the operation teams to study Kubernetes.
  * Although documentation is there, nothing beats actual experience, and most of the problems actually come to light when you have already started.

In short, complexity is the main problem with Kubernetes, but there are some ways to mitigate complexity, and even some unexpected allies.

## Provisioning Kubernetes: cloud providers are your best friends

Provisioning a Kubernetes cluster is actually quite a daunting task. You need machines for the control plane and the data plane (the worker nodes), build some specific OS images and a way to bootstrap the cluster. One common way is to use tools like Kubeadm to bootstrap a cluster.
You should also size properly the control plane, install etcd, install MetalLB if you want to expose services with a Load Balancer, provision a storage infrastructure, install a CNI for the cluster, create periodic backups of etcd and so on...
In short, provisioning a new Kubernetes cluster is really difficult as it involves a lot of decisions in the process.

But let's not panic, as luckily all cloud providers offer a managed Kubernetes cluster as a service!
Let's take Oracle Cloud and the service OKE (Oracle Kubernetes Engine).
With OKE, the whole Control Plane is managed by Oracle, and compared to provisioning an on-prem cluster, you get the following advantages:

* No need to provision machines for the control plane, as the OKE service will take care of it
* No need to think of making the control plane highly available, as OKE offers guaranteed SLAs
* Backup of etcd is done by Oracle automatically every 15 minutes, and restored automatically in case of disruption
* No need to learn Kubeadm, as the bootstrapping process is automated
* No need to install MetalLB, as service of type LoadBalancer will provision a physical Load Balancer by exploiting the OCI Load Balancer service
* No need to provision a storage infrastructure, as there are integration with native Oracle Cloud storage services
* No need to install a CNI, as it is by default provisioned by the OKE service
* No need to install CoreDNS or kube-proxy, as they are already installed and upgraded automatically by Oracle
* No need to build custom OS images for the nodes, as Oracle already gives you pre-built images ready to use
* No need to configure audit logs, they are always enabled and available to inspect
* Easier upgrade process for the whole cluster
* Possibility to automatically scale worker nodes
* Security compliance and certification of the infrastructure
* Support available, as long as you keep your OKE cluster updated
* Integrated Container Registry service for container images
* Possibility to standardize provisioning and do it with the as code approach (oci Terraform provider)

In short, everything is way easier and secured. In addition, if you want more control, you can opt to deploy the control plane using the ClusterAPI provider.

With the help of cloud providers, provisioning a new Kubernetes cluster should take about 15-20 minutes.

## I have got my OKE cluster, so what?

Having the capability to instantly spin up new infrastructure doesn’t always mean that your application developers can take advantage of the new infrastructure in the most optimal way.
Provisioning a Kubernetes cluster is only the first step, and the next step is configuring and administering it.
This step here is where people usually get lost, but here we will try to explain concepts so that they are easily understood and adopting the "as code" strategy.

Generally speaking, there are always 3 kinds of code:

* Application code
* Cluster configurations + Infra applications
* Infrastructure (IaC, Terraform)

Understanding what these codes are and who is responsible for it is essential:

* Application code = Kubernetes manifests to deploy the custom applications built by the Software Development team.
  * This is different from the application source code, as the best practice is to separate the source code and the Kubernetes manifests so that they are in different repositories
  * There should be 1 Git repository for every development team containing the Kubernetes manifests to deploy an application. The development team is the owner of the repository, not the operation team
* Cluster configurations + Infra applications = Kubernetes manifests to deploy infrastructure related applications and configure the OKE cluster
  * Infra applications are those applications that are not developed internally and that serves to maintain the whole cluster.
    * Example: cert-manager is an infra application that will automatically generate certificates and renew them before they expire
  * There should be 1 Git repository dedicated to infra applications and cluster configurations, to be used by the cluster administrators
* IaC Infrastructure = Terraform code to provision an OKE cluster
  * There should be 1 Git repository dedicated to the Terraform infrastructure for the chosen cloud provider

For the IaC infrastructure in Oracle Cloud, you can use also OCI Resource Manager to manage the Terraform state and quickly provision an OKE cluster by using [this stack](../oke-rm)

Next we will focus on the **"cluster administrator"** repository and the way to automate configurations and infra applications provisioning.

## Cluster administration with ArgoCD

ArgoCD is an open source, CNCF graduated project to implement GitOps in Kubernetes clusters.
The base concept is very simple: the ArgoCD controller will be connected to a Git repository and will continuously pull the Kubernetes manifests and deploy them.
So the role of the controller is to keep what is defined as code in the Git repository aligned with the "live" cluster configurations.
The cluster administrators will then configure the cluster through code, and ArgoCD will keep everything in sync and consistent.

With this repository, I want to propose a quick way to install ArgoCD in an OKE cluster and propose a Git template the administer OKE clusters.
This stack will:
* Provision a new OCI DevOps project
* Create 2 OCI Code Repositories: one with pipelines definitions, and another one called "oke-cluster-config" with the git template for the OKE cluster administrators
* Create an OCI Build Pipeline that will mirror the ArgoCD Helm Chart inside the Oracle Cloud Registry, and deploy it in the chosen cluster

[![Deploy to Oracle Cloud](https://oci-resourcemanager-plugin.plugins.oci.oraclecloud.com/latest/deploy-to-oracle-cloud.svg)](https://cloud.oracle.com/resourcemanager/stacks/create?zipUrl=https://github.com/oracle-devrel/technology-engineering/releases/download/oke-gitops-1.1.1/stack.zip)

Once the stack has been provisioned, you can modify the ArgoCD version to deploy by editing the `mirror_argo.yaml` file in the `pipelines` repository.
By default, ArgoCD will be deployed in an "insecure" mode to disable the default SSL certificate, but feel free to modify the chart values in the `argo-cd-chart-values` artifact.