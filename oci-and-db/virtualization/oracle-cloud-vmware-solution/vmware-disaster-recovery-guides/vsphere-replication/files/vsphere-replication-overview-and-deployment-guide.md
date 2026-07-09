# **Disaster Recovery with OCVS**

## DR Models in OCVS

### **Intra-Region DR**

- Deploy separate OCVS SDDCs in different **availability domains (ADs)**  but within the same region.

- Provides resilience against hardware failure or AD-level outages.

### **Inter-Region DR**

- Protect workloads across OCI regions (e.g., **London ↔ Newport**, **Dubai ↔ Abu Dhabi**).

- Replication and recovery occur between two OCVS SDDCs in different OCI regions.

### **Hybrid / On-Prem ↔ OCVS DR**

- Extend an on-premises VMware environment to OCVS.

- Use OCVS as a **failover target** or secondary site without building/maintaining a physical DR datacenter.

VMware have their own built in tools to help with this, the first of which is vSphere Replcation

# OCVS - vSphere Replication 9.x Overview and Deployment Guide

## What is vSphere Replication?

**vSphere Replication** is a hypervisor-based replication and recovery solution, delivered as an extension to **vCenter Server**. It provides **cost-efficient, per-VM protection** without requiring array-based replication.

Unlike traditional storage replication, which depends on identical hardware at both ends, vSphere Replication works at the VMware layer and offers full flexibility in choosing different storage vendors or types across sites.

vSphere Replication can protect virtual machines across several topologies:

- **Site-to-Site Replication**  - Replicate VMs from a primary site to a secondary site for disaster recovery.

- **Intra-Site Replication** - Replicate VMs between clusters within the same site for local resiliency.

- **Multi-Site Replication**  - Replicate VMs from multiple source sites into a shared target site.

---

## Key Benefits

- **Lower Cost per VM** – No need for dedicated array replication licensing.

- **Storage Flexibility** – Protect workloads regardless of the storage vendor at source or target.

- **Simplified Management** – Integrated directly into the vSphere Client and vCenter workflows.

- **Disaster Recovery Ready** – Supports orchestration and non-disruptive DR testing when paired with **Site Recovery Manager (SRM)** or **Live Recovery in VCF 9**.

## Key Features

- **Per-VM Replication** – Protect individual VMs, not entire datastores.

- **Flexible RPO (Recovery Point Objective)** - 5 minutes to 24 hours.

- **Multiple Points in Time (MPIT)** - Option to keep several recovery snapshots.

- **Integrated with vCenter & SRM** - Can be used standalone or with **Site Recovery Manager** for orchestration.

- **Network-efficient** - Uses compression and changed block tracking (CBT) to reduce bandwidth.

- **Encryption of Replication Traffic** - Replication traffic is encrypted before being transmitted.

As of vSphere Replication v9.x there are now 2 modes of replication:

**Enhanced Replication** - New default choice

![EnhancedVR.png](images/EnhancedVR.png)

**Standard Replication** - Legacy choice

![standardVR.png](images/standardVR.png)

| Feature        | Enhanced Replication                                  | Standard Replication                    |
| -------------- | ----------------------------------------------------- | --------------------------------------- |
| Data Path      | Direct to target ESXi host                            | Through a vSphere Replication Appliance |
| Load Balancing | Automated                                             | Manual                                  |
| Minimum RPO    | As low as 1 minute (When used with SRM/Live Recovery) | 5 minutes                               |
| Architecture   | Simplified and optimized                              | Uses a centralized appliance            |
| Status         | Default for new deployments                           | Traditional, being deprecated           |

Most deployments of vSphere Replication are for cross vCenter deployments, across 2 distinct sites.

### Using vSphere Replication Within a Single Site

vSphere Replication does allow for the use of replication within the same vCenter, so you can replicate VMs between clusters as a limited BC/DR solution.

In OCVS this could be done with Cluster 1 being in AD1 and Cluster 2 being in AD2, you would then use vSphere Replication to replicate the VMs in Cluster 1 to Cluster 2 or vice versa.

Cluster 2 would have different storage to Cluster 1. Cluster 1 could be VSAN or OCI Block Storage  and Cluster 2 could also be VSAN or OCI Block Storage. By doing this the replicated VM data is stored on different storage to the original workloads providing resiliency against a cluster/AD outage.

<img title="" src="images/EnhancedVR_singlesite.png" alt="EnhancedVR_singlesite data-align="center">

The downsides of using vSphere Replication in this way is that it requires vCenter to do the recovery of VMs, and if the outage impacts the vCenter server, then recovery becomes harder to do and could possibly require the assistance of VMware support.

### Installing vSphere Replication within OCVS

Contact Oracle Support for access to the vSphere Replication ISO.

Within the ISO there is an ovf and vmdk files that can be used for the deployment. So mount the ISO to gain access to the files

<img title="" src="images/ovf1.png" alt="ovf1.png" data-align="center">

The files marked in Orange are used for the deployment of the first vSphere Replication Appliance (Manager), the Green files are used to deploy addon vSphere Replication Servers, to help with scaling the number of active replications. When you would need to do this would depend on the number of VMs you were replicating and the version of vSphere Replication you were running, as the scaling limits are likely to change with each major release.

Right lick on the host/cluster/resource pool within vCenter and select "Deploy OVF Template"

<img title="" src="images/deployovf.png" alt="deployovf.png" data-align="center">

You will then be prompted to select the required files as shown below

![ovfselectfiles.png](images/ovfselectfiles.png)

![Screenshot_1.png](images/Screenshot_1.png)

![Screenshot_2.png](images/Screenshot_2.png)

You then follow the prompts, and you will eventually be asked to pick the network for the OVF deployment

You can put it in any network you like, as long as the required networking ports are allowed. The easiest option as per the screenshot below is to put it into the same network and the vSphere Management components.

<img title="" src="images/Screenshot_3.png" alt="Screenshot_3.png" data-align="center">

You will then be required to fill in the deployment details such as admin/root passwords and networking IP details.

<img title="" src="images/Screenshot_4.png" alt="Screenshot_4.png" data-align="center">

Once it has been deployed and powered on, you can then access the management interface on port 5480 as shown here using the admin/root login and password that was configured during the appliance deployment.

<img title="" src="images\Screenshot_5.png" alt="Screenshot_5.png" data-align="center">

You will then have to configure vSphere Replication and connect it to the local vCenter/PSC.

<img title="" src="images/configure_appliance.png" alt="configure appliance .png" data-align="center">

<img title="" src="images/Screenshot_6.png" alt="SScreenshot_6.png" data-align="center">

You will accept the security certificate.

<img title="" src="images/Screenshot_7.png" alt="Screenshot_7.png" data-align="center">

and configure the site name.

<img title="" src="images/Screenshot_8.png" alt="Screenshot_8.png" data-align="center">

After it has been configured you will see the following

<img title="" src="images/Screenshot_9.png" alt="Screenshot_9.png" data-align="center">

When you login vCenter you will see the Site Recovery Plugin has been deployed

<img title="" src="images/Screenshot_10.png" alt="Screenshot_10.png" data-align="center">

<img title="" src="images/SiteRecovery.png" alt="SiteRecovery.png" data-align="center">

**If at this point you see errors in vCenter regarding the plugin failed to download, this is most likely a DNS issue of some kind. If in OCI/OCVS please ensure the correct A records are present for the VR appliances in OCVS and on prem in the OCVS VCN. This way it ensures the vCenter can reach them correctly**

<img title="" src="images/Screenshot_11.png" alt="Screenshot_11.png" data-align="center">

<img title="" src="images/Screenshot_12.png" alt="Screenshot_12.png" data-align="center">

By default, you will have the option to configure replications within the same vCenter. 

**If you wish to do cross site replication for DR, you will follow these exact same steps at the remote site and then you would configure a pairing between sites.**

Once this has been completed you are able to configure a new site pairing between the 2 vCenters

<img title="" src="images/sitepairing.png" alt="sitepairing.png" data-align="center">

You have the option to peer with a vCenter in the same or different SSO domain, with OCVS it is most likely that your vCenter servers/SDDCs will be in different vSphere SSO domains.

![Screenshot_13.png](images/Screenshot_13.png)

<img title="" src="images/Screenshot_14.png" alt="Screenshot_14.png" data-align="center">

It will then check the remote vCenter and confirm that vSphere Replication has been installed and configured with that remote vCenter.

<img title="" src="images/Screenshot_15.png" alt="Screenshot_15.png" data-align="center">

<img title="" src="images/Screenshot_16.png" alt="Screenshot_16.png" data-align="center">

Once the pairing has completed successfully you will then be presented with the following screen, and you can login to start configuring replications

![sitepairingcomplete.png](images/sitepairingcomplete.png)

<img title="" src="images/Screenshot_17.png" alt="Screenshot_17.png" data-align="center">

When configuring replications for VMs, you will be offered the choice between Standard and Enhanced Replication, the default should always be Enhanced for new replications.

You will select the VMs you wish to replicate and protect.

![Screenshot_18.png](images/Screenshot_18.png)

Select the destination datastore for the replicated VMDK and VM files

<img title="" src="images/Screenshot_19.png" alt="Screenshot_19.png" data-align="center">

Test mappings to confirm there are no errors.

<img title="" src="images/Screenshot_20.png" alt="Screenshot_20.png" data-align="center">

Configure replication settings such as RPO/Snapshots, compression and encryption.

![Screenshot_21.png](images/Screenshot_21.png)

Once this has been completed you will see this screen

<img title="" src="images/Screenshot_22.png" alt="Screenshot_22.png" data-align="center">

and in vCenter you will see the following

<img title="" src="images/Screenshot_23.png" alt="Screenshot_23.png" data-align="center">

**If at this point the progress bar stays at 0%, or you get an error which states "No connection to VR Server" this is a routing/firewall issue.**

Troubleshooting steps are shown in this [kb](https://knowledge.broadcom.com/external/article/384776/no-connection-to-vr-server-for-virtual-m.html#:~:text=This%20issue%20typically%20has%20widespread,the%20network%2C%20firewall%2C%20etc.).

For within OCVS it is most likely because vmk3 is configured for replication but it is not routable, this works fine with the legacy replication option with VR but does not work for Enhanced Replication.

You have 3 options:

- Disable vSphere Replication on vmk3 and enable it on vmk0 which is also for management. This is the preferred option, as this will allow it to be routable. as long as the route table and NSG in the OCVS VCN allow it to be. Enhanced Replication is encrypted by default between the host at the source and the host at the destination so there is no need to worry about the data in transit, there should also be no bandwidth worries either as OCVS hosts have either 25/50/100Gb network adaptors.
- Create a new TCP/IP stack on every host for Replication. This would allow the VR traffic to be routable as well. Follow this [article](https://techdocs.broadcom.com/us/en/vmware-cis/vsphere/vsphere/8-0/vsphere-networking-8-0/setting-up-vmkernel-networking/create-a-custom-tcp-ip-stack.html)
- Use static routes on each ESXi host - This will force VR traffic to follow a specific route. Follow this [kb](https://knowledge.broadcom.com/external/article/308786/configuring-static-routes-for-vmkernel-p.html)

**Also Enhanced replications require TCP network connectivity on ports 31031 and 32032 from the ESXi hosts on which the replicated VMs are running to the ESXi hosts of the cluster containing the target datastore. Make sure your route tables and NSGs in the OCVS VCN are configured accordingly and the same is done for on prem (if required).**

**For further port connectivity info please visit [vSphere Replication - VMware Ports and Protocols](https://ports.broadcom.com/home/vSphere-Replication)**

### Failover

To failover a VM or multiple VMs, you must log into Site Recovery at the destination.

<img title="" src="images/Screenshot_24.png" alt="Screenshot_24.png" data-align="center">

Then select the **Incoming Replications**, right click on the VM you want to recover and select **Recover.**

<img title="" src="images/Recover.png" alt="Recover.png" data-align="center">

You will now be presented with 2 options:

<img title="" src="images/Screenshot_25.png" alt="Screenshot_25.png" data-align="center">

* Syncronise recent changes - This is if the source site is still active and the source VM is powered off. If both these requirements are met, it will do an offline sync and copy the changes from the last RPO sync, making sure you have the latest data available.

You have the option to have the VM power on after recovery, this is enabled by default but it is optional. As you will need to ensure there is no chance of MAC Address/IP conflicts.

If you do not meet the criteria as mentioned, you will be given an error message as follows:

<img title="" src="images/Screenshot_26.png" alt="Screenshot_26.png" data-align="center">

You will then have to use option 2, which will use whatever data has already been replicated and recover using only this.

You can now decide on which folder the recovered VM will sit in under the destination vCenter

<img title="" src="images/Screenshot_27.png" alt="Screenshot_27.png" data-align="center">

Now you can pick which cluster/host/resource pool the VM will sit in

<img title="" src="images/Screenshot_28.png" alt="Screenshot_28.png" data-align="center">

As mentioned in the yellow box, the recovered VM will not be connected to any network, this is done to avoid all possible chances of conflict across the network. So as part of your recovery process you will have to connect the VMs vnic to the required network after the recover has completed.

![Screenshot_29.png](images/Screenshot_29.png)

The VM will now be added to the inventory in the vCenter and powered on if that option was selected. 

The vSphere Replication interface will now show it as a **Recovered VM**

<img title="" src="images/Screenshot_30.png" alt="Screenshot_30.png" data-align="center">

In vCenter you will see the following tasks/events on the recovered VM

<img title="" src="images/Screenshot_31.png" alt="Screenshot_31.png" data-align="center">

### Failback

Is a very similar process to failover.

At the destination side, where the VM was recovered to, you would select outgoing replications and configure a new replication.

<img title="" src="images/Screenshot_32.png" alt="Screenshot_32.png" data-align="center">

![Screenshot_33.png](images/Screenshot_33.png)

If the original source VM is still in the inventory of the vCenter, you can remove it from the inventory *but do not delete from disk**. The vmdks can now be used as seeds, so only replicated changes need to be transferred minimizing the amount of time and b/w needed to get the replication running.

If this has been done correctly you will see the following information and be given the option to **select seeds**

<img title="" src="images/Screenshot_34.png" alt="Screenshot_34.png" data-align="center">

vSphere Replication will automatically map the seed disks, but if for some reason it maps them incorrectly you can modify the selection. **please be careful as if you map them incorrectly it could cause unrecoverable data loss.**

![Screenshot_35.png](images/Screenshot_35.png)

Select the RPO schedule just as before.

![Screenshot_36.png](images/Screenshot_36.png)

Confirm everything and select **Finish.**

<img title="" src="images/Screenshot_39.png" alt="Screenshot_39.png" data-align="center">

As the replication is being redone, you can monitor its progress and see how much data it is transferring along with its verification of the seed data

![Screenshot_40.png](images/Screenshot_40.png)

Thank you for joining me on this journey into vSphere Replication v9.x
