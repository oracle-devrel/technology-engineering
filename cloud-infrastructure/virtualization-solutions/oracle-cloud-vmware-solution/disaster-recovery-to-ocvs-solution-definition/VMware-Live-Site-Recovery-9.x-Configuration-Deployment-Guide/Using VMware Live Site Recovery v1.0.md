# VMware Live Site Recovery (9.x) Configuration and Deployment Guide

### Introduction

VMware Live Site Recovery (formerly VMware Site Recovery Manager) provides simplified disaster recovery orchestration and testing for workloads running on VMware environments. It integrates tightly with the VMware stack within OCVS, to deliver automated failover, failback, and non-disruptive recovery testing. 

When the product was called Site Recovery Manager (SRM), it worked with a separate product called vSphere Replication (VR). vSphere Replication was essentially a free product that replicated VM data, Site Recovery Manager helped orchestrate the failover and failback and testing of the VMs. So both products would come together to give you a fully fledged DR solution for your VMware environment.

Now with VMware Live Recovery (VLR), vSphere Replication is still a standalone product that can be used, but when you install VLR the appliance includes VR already saving you the additional steps of deploying it separately.

## Prerequisites

Before starting, ensure the following:

- **Protected and Recovery Sites** are deployed and paired.

- **vSphere Replication** or array-based replication is configured between sites.

- Appropriate **network mappings, folder mappings, and resource mappings** are defined.

- You have sufficient **permissions** in vCenter/Live Recovery.

- An application or VM is already configured for replication

Before you can use the product it needs to be deployed at both sites and paired between sites. which is what we will cover first.

## Deploying VMware Live Recovery Appliance.

When you access the VMware/Broadcom portal you will be able to download the Live Recovery ISO file.

This then needs to be mounted on a jump box that has access to the local vCenter.

In the vCenter right click on the cluster object and select **Deploy OVF Template** 

<img title="" src="images/Screenshot%202025-09-15%20154113.png" alt="Screenshot 2025-09-15 154113.png" data-align="center">

Now select the **Local File**

<img title="" src="images/Screenshot%202025-09-15%20154238.png" alt="Screenshot 2025-09-15 154238.png" data-align="center">

**The VLSR iso needs to be mounted, and inside the iso there is a bin folder which contains the required files.** 

Now select the file files from the bin folder

<img title="" src="images/Screenshot%202025-09-12%20101935.png" alt="Screenshot 2025-09-12 101935.png" data-align="center">

Now work through the rest of the steps as shown in the screenshots

![Screenshot 2025-09-12 102004.png](images/Screenshot%202025-09-12%20102004.png)

Select which compute resource the OVF will be deployed into

![Screenshot 2025-09-12 102010.png](images/Screenshot%202025-09-12%20102010.png)

Confirm the details of the appliance

![Screenshot 2025-09-12 102030.png](images/Screenshot%202025-09-12%20102030.png)

Accept the license agreement

![Screenshot 2025-09-12 102047.png](images/Screenshot%202025-09-12%20102047.png)

Select the storage the OVF will be deployed onto

![Screenshot 2025-09-12 102054.png](images/Screenshot%202025-09-12%20102054.png)

Select the VDS/VSS network the appliance will use once deployed

![Screenshot 2025-09-12 102108.png](images/Screenshot%202025-09-12%20102108.png)

Configure the appliance, including all passwords, DNS/NTP etc.

![Screenshot 2025-09-12 102132.png](images/Screenshot%202025-09-12%20102132.png)

![Screenshot 2025-09-12 104816.png](images/Screenshot%202025-09-12%20104816.png)

Once it has been deployed you can power it on and if everything has been done correctly you will be able to login to its management interface, https://applianceIP/FQDN:5480 and you will be presented with the option to configure the appliance further

![Screenshot 2025-09-12 105330.png](images/Screenshot%202025-09-12%20105330.png)

This is where you have to pair it to the local vCenter (Configure Appliance) with a login that meets the requirements (in most cases customers use adminsitrator@vsphere.local or similar)

Once that has been done, you will be presented with the following screen

![Screenshot 2025-09-12 103344.png](images/Screenshot%202025-09-12%20103344.png)

You will then see the VMware Live Site Recovery Plugins be deployed into the vCenter

<img title="" src="images/Screenshot%202025-09-12%20104141.png" alt="Screenshot 2025-09-12 104141.png" data-align="center">

This will then take you to the Live Recovery Landing page, which will confirm the status of VLR in general for the site

![Screenshot 2025-09-12 104146.png](images/Screenshot%202025-09-12%20104146.png)

Once you have selected **OPEN VMware Live Site Recovery** you will be shown the current Site Pair, this will allow you to use vSphere Replication within the same vCenter, for example if you wanted to protect VMs between clusters.

<img title="" src="images\Screenshot%202025-09-12%20105714.png" alt="Screenshot 2025-09-12 105714.png" data-align="center">

Now we have confirmed that this is working as expected, we can now repeat the process at the Recovery Site.

Once that has been completed we can continue from the source site and create a **New Site Pair**

<img src="images\Screenshot%202025-09-12%20105714._1png.png" title="" alt="Screenshot 2025-09-12 105714._1png.png" data-align="center">

You will now be asked to pair with a vCenter in the same SSO domain or in a different SSO domain. **In most cases it will be a different SSO domain.**

![Screenshot 2025-09-12 105721.png](images/Screenshot%202025-09-12%20105721.png)

Now enter in the credentials of the remote vCenter Server 

<img title="" src="images/Screenshot%202025-09-12%20105740.png" alt="Screenshot 2025-09-12 105740.png" data-align="center">

You will have to accept the TLS certificates

<img title="" src="images/Screenshot%202025-09-12%20105745.png" alt="Screenshot 2025-09-12 105745.png" data-align="center">

It will then confirm that the site you are pairing with has its own instance of VLSR/VR

<img title="" src="images/Screenshot%202025-09-12%20105801.png" alt="Screenshot 2025-09-12 105801.png" data-align="center">

Now confirm you are ready for the pair to complete

<img title="" src="images/Screenshot%202025-09-12%20114439.png" alt="Screenshot 2025-09-12 114439.png" data-align="center">

If you have ever used VR on its own, you will recognise this is a very similar process.

You will now see that there are 2 pairings visible

The first is the pairing between our 2 SDDCs, while the other is a the local pairing allowing for replication within the same site/vCenter

<img src="images\Screenshot%202025-09-12%20114509.png" title="" alt="Screenshot 2025-09-12 114509.png" data-align="center">

After selecting **View Details** you will be presented with the VLSR overview, you will be prompted for the login details for the remote site

<img title="" src="images/Screenshot2025-09-15115553.png" alt="Screenshot2025-09-15115553.png" data-align="center">

Key things to note with this new version is that, when you select **Replication Servers** you will see the ESXi hosts listed at each site. As with v9.x the ESXi communicate with each other directly for replication purposes using the Enhanced Replication feature by default.

<img src="images\Screenshot%202025-09-15%20115604.png" title="" alt="Screenshot 2025-09-15 115604.png" data-align="center">

<img src="images\Screenshot%202025-09-15%20115611.png" title="" alt="Screenshot 2025-09-15 115611.png" data-align="center">

Enhanced Replication requires that the ESXi hosts at both sides can communicate with each other directly, and the replication data between hosts is encrypted by default. Currently with OCVS vmk3 on each ESXi host is configured for replication, but does not have its own TCP/IP stack and this create a problem.

You have 3 options:

- Disable vSphere Replication on vmk3 and enable it on vmk0 which is also for management. This is the preferred option, as this will allow it to be routable. as long as the route table and NSG in the OCVS VCN allow it to be. Enhanced Replication is encrypted by default between the host at the source and the host at the destination so there is no need to worry about the data in transit, there should also be no bandwidth worries either as OCVS hosts have either 25/50/100Gb network adaptors.
- Create a new TCP/IP stack on every host for Replication. This would allow the VR traffic to be routable as well. Follow this [article](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/vsphere-networking-8-0/setting-up-vmkernel-networking/create-a-custom-tcp-ip-stack.html)
- Use static routes on each ESXi host - This will force VR traffic to follow a specific route. Follow this [kb](https://knowledge.broadcom.com/external/article/308786/configuring-static-routes-for-vmkernel-p.html)

**Also Enhanced replications require TCP network connectivity on ports 31031 and 32032 from the ESXi hosts on which the replicated VMs are running to the ESXi hosts of the cluster containing the target datastore. Make sure your route tables and NSGs in the OCVS VCN are configured accordingly and the same is done for on prem (if required).**

**For further port connectivity info please visit [vSphere Replication - VMware Ports and Protocols](https://ports.broadcom.com/home/vSphere-Replication)**

You are now able to do performance tests between sites, to see the status of the connection and basic performance metrics

<img title="" src="images/Screenshot%202025-09-15%20115803.png" alt="Screenshot 2025-09-15 115803.png" data-align="center">

### Resource Mappings

The key thing about VLSR and how it helps handle DR failovers, is with the use of **Resource Mappings**. This allows VLR to failover VMs and know exactly where to place them at the destination site during the failover process.

<img title="" src="images/Screenshot%202025-10-01%20134150.png" alt="Screenshot 2025-10-01 134150.png" data-align="center">

We will now go through and create the Network Mappings

You have the ability to let it auto configure them for you to save time

<img title="" src="images/Screenshot%202025-09-15%20115833.png" alt="Screenshot 2025-09-15 115833.png" data-align="center">

As you can see here, it has auto populated the most obvious ones, but you are able to edit/amend as required

<img title="" src="images/Screenshot%202025-09-15%20115941.png" alt="Screenshot 2025-09-15 115941.png" data-align="center">

It can also populate the reverse mappings. The reverse mappings are for when you want it fail back to the primary site after the DR event is over. So VLR knows where to place the VMs on the return trip. Normally this would just be an exact mirror of what the original mappings were, but there may be use cases where this may not be the case.

<img title="" src="images/Screenshot%202025-09-15%20115959.png" alt="Screenshot 2025-09-15 115959.png" data-align="center">

We will now move onto the Folder Mappings

Its a very similar process to the Network Mappings we did earlier

<img title="" src="images/Screenshot%202025-09-15%20120029.png" alt="Screenshot 2025-09-15 120029.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120047.png" alt="Screenshot 2025-09-15 120047.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120055.png" alt="Screenshot 2025-09-15 120055.png" data-align="center">

Now we do the same thing but for the Host Resource Mappings

<img title="" src="images/Screenshot%202025-09-15%20120131.png" alt="Screenshot 2025-09-15 120131.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120144.png" alt="Screenshot 2025-09-15 120144.png" data-align="center">

If you are using VSAN you can do the same thing for VSAN Storage Polices as well.

<img title="" src="images/Screenshot%202025-09-15%20120203.png" alt="Screenshot 2025-09-15 120203.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120321.png" alt="Screenshot 2025-09-15 120321.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120329.png" alt="Screenshot 2025-09-15 120329.png" data-align="center">

### Placeholder Datastores

Part of the initial configuration process is to select **Placeholder Datastores**, these can be tiny dedicated datastores or can use existing datastores at either site. The goal is to for these placeholder datastores to hold the placeholder configuration data for the VMs being replicated, not the actual replicated data themselves.

<img title="" src="images/Screenshot%202025-09-15%20120358.png" alt="Screenshot 2025-09-15 120358.png" data-align="center">

In this example we will be removing one of the datastores so that VLSR can not use it for placeholder information. We are not deleting it from vCenter or anything like that, we are just removing it as a selection option for VLSR to use.

<img title="" src="images/Screenshot%202025-09-15%20120404.png" alt="Screenshot 2025-09-15 120404.png" data-align="center">

[Select a Placeholder Datastore](https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/live-site-recovery/9-0/how-do-i-protect-my-environment/about-placeholder-virtual-machines/configure-a-placeholder-datastore.html) For further information 

## Configuring Replications

Now lets configure some replications quickly using vSphere Replication

<img title="" src="images/Screenshot%202025-09-15%20120726.png" alt="Screenshot 2025-09-15 120726.png" data-align="center">

Select the VMs you would like to replicate

<img title="" src="images/Screenshot%202025-09-15%20120749.png" alt="Screenshot 2025-09-15 120749.png" data-align="center">

Pick target Datastore

<img title="" src="images/Screenshot%202025-09-15%20120800.png" alt="Screenshot 2025-09-15 120800.png" data-align="center">

Test connectivity between replication hosts

<img title="" src="images/Screenshot%202025-09-15%20120808.png" alt="Screenshot 2025-09-15 120808.png" data-align="center">

Configure the RPO

<img title="" src="images/Screenshot%202025-09-15%20120821.png" alt="Screenshot 2025-09-15 120821.png" data-align="center">

You now have the option to create a Protection Group now or later (we will do it later)

<img title="" src="images/Screenshot%202025-09-15%20120842.png" alt="Screenshot 2025-09-15 120842.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120852.png" alt="Screenshot 2025-09-15 120852.png" data-align="center">

You will now see the VMs being replicated int he VLSR dashboard

<img title="" src="images/Screenshot%202025-09-15%20120905.png" alt="Screenshot 2025-09-15 120905.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20120918.png" alt="Screenshot 2025-09-15 120918.png" data-align="center">

## Protection Groups

The next thing to consider is **Protection Groups**

Protection Groups are about placing VMs together in a logical container so they are considered as one group. This is normally done when VMs in a certain App would be best failed over together, or VMs in the same VLAN could be in the same Protection Group

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/live-site-recovery/9-0/how-do-i-protect-my-environment/creating-and-managing-protection-groups.html

<img title="" src="images/Screenshot%202025-09-15%20120447.png" alt="Screenshot 2025-09-15 120447.png" data-align="center">

You can pick the direction that the Protection Group will work in, as some customers will have VMs at Site A they want to failover to Site B and VMs at Site B they want to failover to Site B (a more active/active approach)

<img title="" src="images/Screenshot%202025-09-15%20120532.png" alt="Screenshot 2025-09-15 120532.png" data-align="center">

We are using vSphere Replication within OCVS

<img title="" src="images/Screenshot%202025-09-15%20120541.png" alt="Screenshot 2025-09-15 120541.png" data-align="center">

If replications have been configured correctly you will see the option below showing all the VMs currently being replicated for you to add as required

 <img src="images\Screenshot%202025-09-15%20120952.png" title="" alt="Screenshot 2025-09-15 120952.png" data-align="center">

**If you see a screen showing ZERO VMs, it means you have not actually configured vSphere Replication to Replicate any VMs.** This needs to be done first otherwise there are no VMs to add into the Protection Group.

You now have the option to create a Recovery Plan now or later ( we will create this later)

<img title="" src="images/Screenshot%202025-09-15%20121002.png" alt="Screenshot 2025-09-15 121002.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121009.png" alt="Screenshot 2025-09-15 121009.png" data-align="center">

## **Recovery Plans**

A recovery plan functions as an automated runbook that orchestrates the entire recovery process. It defines the sequence in which VMware Live Site Recovery powers on and shuts down virtual machines, assigns network settings to recovered VMs, and manages other key operations. Recovery plans are highly configurable to meet specific requirements.

Each recovery plan is built around one or more protection groups. A single protection group can be referenced by multiple recovery plans. For example, you might have one plan for a full organizational migration and additional plans tailored to specific departments. This structure allows flexible recovery workflows using the same underlying protection groups, enabling different recovery scenarios without duplicating configuration.

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/live-site-recovery/9-0/how-do-i-protect-my-environment/creating-testing-and-running-recovery-plans.html

**Only a single Recovery Plan can be run at any onetime**

### Creating a Recovery Plan

Select **New Recovery Plan** 

<img title="" src="images/Screenshot%202025-09-15%20121031.png" alt="Screenshot 2025-09-15 121031.png" data-align="center">

Give the Recovery Plan a name

<img title="" src="images/Screenshot%202025-09-15%20121044.png" alt="Screenshot 2025-09-15 121044.png" data-align="center">

Select the Protection Group(s) you would like to be contained within the Recovery Plan

<img title="" src="images/Screenshot%202025-09-15%20121051.png" alt="Screenshot 2025-09-15 121051.png" data-align="center">

Here you can select what networks will be used when you run a **test**. When doing DR tests customer usually like to attach the VMs to a custom network or use isolated networks to ensure that the VMs do not conflicts with live production systems

<img title="" src="images/Screenshot%202025-09-15%20121058.png" alt="Screenshot 2025-09-15 121058.png" data-align="center">

Select **Finish**

<img title="" src="images/Screenshot%202025-09-15%20121107.png" alt="Screenshot 2025-09-15 121107.png" data-align="center">

You will now see the new Recovery Plan created and listed

<img title="" src="images/Screenshot%202025-09-15%20121115.png" alt="Screenshot 2025-09-15 121115.png" data-align="center">

#### Modifying a recovery plan

Recovery Plans can be edited and there are a multitude of options to help configure the recovery process

<img title="" src="images/Screenshot%202025-09-15%20122427.png" alt="Screenshot 2025-09-15 122427.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20122435.png" alt="Screenshot 2025-09-15 122435.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20122444.png" alt="Screenshot 2025-09-15 122444.png" data-align="center">

Further details can be found here:

https://techdocs.broadcom.com/us/en/vmware-cis/live-recovery/live-site-recovery/9-0/how-do-i-protect-my-environment/configuring-a-recovery-plan/recovery-plan-steps.html

### Running the Recovery Plan

Select the Recovery Plan you wish to use and select **Run** or ***Test***

#### Test

<img title="" src="images/Screenshot%202025-09-15%20121147-1.png" alt="Screenshot 2025-09-15 121147-1.png" data-align="center">

In our example we will be running a test

You have the option to replicate recent changes, depending on your RPO schedule and last replication cycle for the VMs, this could take some time.

<img title="" src="images/Screenshot%202025-09-15%20121155.png" alt="Screenshot 2025-09-15 121155.png" data-align="center">

Select **Finish**

<img title="" src="images/Screenshot%202025-09-15%20121203.png" alt="Screenshot 2025-09-15 121203.png" data-align="center">

When you check in the destination sites vCenter, you will see that the VM(s) have been recovered, and they are attached to an isolated port group

<img title="" src="images/Screenshot%202025-09-15%20121318-1.png" alt="Screenshot 2025-09-15 121318-1.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121252.png" alt="Screenshot 2025-09-15 121252.png" data-align="center">

In VLSR it will show the Test as being complete

<img title="" src="images/Screenshot%202025-09-15%20121331.png" alt="Screenshot 2025-09-15 121331.png" data-align="center">

Once you are happy that the test can be cleared down, in the VLSR console you can select **Cleanup**

<img title="" src="images/Screenshot%202025-09-15%20121337.png" alt="Screenshot 2025-09-15 121337.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121345.png" alt="Screenshot 2025-09-15 121345.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121404.png" alt="Screenshot 2025-09-15 121404.png" data-align="center">

The Recovery Plan will be put back into a ready state.

<img title="" src="images/Screenshot%202025-09-15%20121430.png" alt="Screenshot 2025-09-15 121430.png" data-align="center">

#### Run Failover

In this example we will run the actual Recovery Plan, just like if we were going to run it in a real live DR scenario.

<img title="" src="images/Screenshot%202025-09-15%20121147-1.png" alt="Screenshot 2025-09-15 121147-1.png" data-align="center">

The key difference between a Planned Migration and Disaster Recovery options are:

- Planned Recovery assumes that the source site is still up and running and data can still be replicated, and if any errors happen it will halt the process. 

- Disaster Recovery assumes the source site is down and it will still try to replicate recent data but if it cant, it will continue on regardless of errors.

<img title="" src="images/Screenshot%202025-09-15%20121439.png" alt="Screenshot 2025-09-15 121439.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121454.png" alt="Screenshot 2025-09-15 121454.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121521.png" alt="Screenshot 2025-09-15 121521.png" data-align="center">

As you can see the VMs have been powered on as part of the Recovery Plan execution and the network for the VM vnic is detached, this is how the Recovery Plan was set to run and how my mappings were configured in the earlier steps.

<img title="" src="images/Screenshot%202025-09-15%20121652.png" alt="Screenshot 2025-09-15 121652.png" data-align="center">

In the VLSR console you can inspect the recovery steps

<img title="" src="images/Screenshot%202025-09-15%20121707.png" alt="Screenshot 2025-09-15 121707.png" data-align="center">

You will see that the recovery process has completed

<img title="" src="images/Screenshot%202025-09-15%20121736.png" alt="Screenshot 2025-09-15 121736.png" data-align="center">

#### Reprotect

After you have failed over, the DR site has become the Primary Site and the original site is now going to be the classed as the Recovery Site.

The VMs need to be protected again and replication needs to be reversed to ensure the recovered VMs are protected again.

**Reprotect reverses the direction of protection using the configuration defined prior to the original recovery. **This process can only be initiated once the recovery has completed successfully without errors. If any errors occur during recovery, they must be resolved and the recovery rerun until it completes cleanly.**

**If you did a full DR failover, once the original site is available a gain, you must run a Planned Migration operation, so VSLR at both sites, is fully in sync and all errors have been resolved.****

During reprotection with vSphere Replication, VLSR leverages the original VMDK files as seed copies. The full sync phase primarily involves checksum validation, resulting in minimal actual data transfer over the network.

Initiating synchronization from the new protected site to the new recovery site ensures the recovery site holds an up-to-date copy of the virtual machines. This guarantees that recovery operations can begin immediately once reprotect completes.

If you need to configure reverse replication manually, use the VMware Live Site Recovery UI to force-stop the incoming replication group on the former recovery site (now the protected site). Avoid deleting the VM from the original protected site, as doing so will cause reprotect to fail.

After reprotect is complete, you can run tests to validate that the updated configuration between the protected and recovery sites is functioning as expected.

Depending on the state of the original/primary site this process may not be possible for a while, you just have to understand that the newly recovered VMs will be unprotected for this period

<img title="" src="images/Screenshot%202025-09-15%20121745.png" alt="Screenshot 2025-09-15 121745.png" data-align="center">

<img title="" src="images/Screenshot%202025-09-15%20121751.png" alt="Screenshot 2025-09-15 121751.png" data-align="center">

![Screenshot 2025-09-15 121851.png](images/Screenshot%202025-09-15%20121851.png)

Once the reprotect operation has been completed, the Recovery Plan will be ready to use. You can run Test and Failover operations as normal 
