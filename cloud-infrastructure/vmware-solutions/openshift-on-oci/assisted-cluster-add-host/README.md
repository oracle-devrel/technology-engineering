# Adding a Host to an Assisted Installed OpenShift Cluster on Oracle Cloud (OCI)

This guide provides detailed instructions on adding a host to an OpenShift cluster installed via the Assisted Installer, specifically in the Oracle Cloud Infrastructure (OCI). The process includes generating a discovery ISO, creating a custom image, configuring OCI load balancers, launching a new instance, and approving the host in the OpenShift console.

---

## Prerequisites

Before starting, ensure the following:

- A functioning OpenShift cluster installed via the Assisted Installer on OCI.
- You have access to the OpenShift Assisted Cluster and the OpenShift console.
- You have privileges to manage instances and load balancers within OCI


## Steps
### 1. Create Add Host Discovery ISO

1. Log in to the **OpenShift Console** (https://console.redhat.com/openshift/), go to your cluster list and select your cluster.
2. Navigate to **Add Hosts** tab.

<img src="files/1. clusteroverview.png" width=300x align="top">|<img src="files/2. addHost1.png" width=300x align="top">

3. Click on **Add Host** button.
4. Follow the wizard to configure and generate the **Discovery ISO**, you can add an SSH public key to this ISO if you later require direct SSH access.
5. Once the ISO is generated, download it locally. 

<img src="files/3. DownloadISO.png" width=300x align="top">

### 2. Create Custom Image in Oracle Cloud (OCI) Based on Add Host Discovery ISO

OCI requires a custom image to boot a new instance with the Discovery ISO embedded. This is a different ISO that what was used for creating the initial cluster!

#### Create Custom Image Using OCI Commands or Console

1. **Upload the ISO to an Object Storage Bucket**:
   - Upload the discovery ISO to an OCI Object Storage bucket in your tenancy.
   - <img src="files/4. uploadISO.png" width=300x align="top">

2. **Create a Custom Image from the Discovery ISO**:
   - Go to **Compute > Custom Images** (in the OCI Console)
   - Click **Import-discovery-image`
     - **Operating System**: RHEL
     - **Bucket / Object Name**: Select the bucket where you uploaded the ISO file and select under object name the ISO file.
   - Set the **Image Type** to: QCOW2
   - Set the **Launch Mode** to: Paravirtualized mode
   - click on **Import image**
   - <img src="files/5. importImage.png" width=300x align="top">

3. **Modify Image Capabilities** 
    - After the custom image is created, click on **Edit image capabilities**
    - Set the firmware available options to ONLY **UEFI_64**
    - <img src="files/6. editImageCapabilities.png" width=300x align="top">


### 3. Modify the Oracle Cloud Infrastructure (OCI) Load Balancer

To allow the new host to communicate with the OpenShift cluster, you need to modify your OCI OpenShift APP Load Balancer to allow traffic on port **22624**. This port is used for Machine Config Server (MCS) communication. By default only the internal API load balancer is configured for this.

1. Navigate to **Networking > Load Balancer**.
2. Select the **api apps** load balancer used by your OpenShift cluster.
3. Create a new backend set and set the health check to:
    - Protocol: HTTP
    - Port: 22624
    - Interval: 10000
    - Timeout: 3000
    - Number of retries: 3
    - Status code: 200
    - URL path: /healthz
    - response: .*
    - <img src="files/7. CreateBackend.png" width=300x align="top">

4. Add the Management Nodes to this backend set, by clicking on the **Add Backends** option. Set the port for each backend to 22624.

<img src="files/8. AddBackenNodes.png" width=400x align="top">

    
5. Wait until your backend is in healthy state, then under **Listeners** menu, add a istener to:
   - Allow incoming traffic on port **22624** (Machine Configuration).
   - Ensure the listener forwards this traffic to the newly created backend.

<img src="files/9. CreateListener.png" width=400x align="top">

5. Modify the NSG (Network Security Group) assigned to this load balancer to allowin incomming traffic on TCP/22624 from the intenal VCN Network
   - Go to the main page of the load balancer
   - In the Load Balancer Information section you will see the assigned NSG. Click on this NSG
   - Add a rule for incoming (ingress) traffic. Set the source CIDR range to the CIDR range of your VCN. The Protocol to TCP and destination port to 22624
   - <img src="files/10. NSG-LB.png" width=500x align="top">


### 4. Launch a New Instance Using the Custom Image

Once the custom image is created and the load balancer is configured, you can launch a new instance as worker node that will register with the OpenShift cluster.

1. In the **OCI Console**, go to **Compute > Instances**.
2. Click **Create Instance** and configure the instance:
   - **Image**: Choose the custom image you created (`openshift-discovery-image`).
   - **Shape**: Select an appropriate shape (e.g., VM.Standard.E4.Flex).
   - **Network**: Attach the instance to the correct VCN and subnet that the OpenShift cluster uses. Usse the private subnet for your instance.
   - It is recommended to have an openshift worknode with min 4 cores and 16 GB Ram.
   - The worker node needs at minimum a 100GB Disk and it is recommended to have this 30 VPUs assigned
   - Click on **create** to launch the instance

<img src="files/11. AddNode1.png" width=300x align="top"> | <img src="files/12. AddNode2.png" width=300x align="top">

3. **NSG Assignment**: When the node is being created you can click on the **edit** link behing the Network Security Groups in the primary VNIC section.
   - Set the NSG to the NSG for the Openshift Worker Nodes (cluster-compute-nsg)
   - <img src="files/13. NodeSetNSG.png" width=300x align="top">

4. **Set the correct tag**: After the instance is up an running (Green: Running state). Add the correct openshift tag
   - Navigate to **[More Actions]** on the main page of the instance 
   - Click on **Add Tags**
   - Select the Tag Namespace used for this Openshift cluster. Likely the name of your cluster
   - Set the tag key to **compute**
   - <img src="files/14. AddTag.png" width=300x align="top">

### 5. Install ready nodes in the Openshift console (https://console.redhat.com/openshift/)

It will take a few minutes, but at somepoint your new node should show on the **Add hosts** tab. Wait for the host to become in the **Ready state**. It likely will first show **Insufficient**, just be patient. 

When the node is in ready state, you can click on the **[Install Ready Nodes]**

<img src="files/15. WaitNodeReady.png" width=400x align="top">

This will take some time. When it get to the **Installed** state, the node will reboot and after a few minute shoud up as node in your Cluster Console.

### 5. Approve the Host in the OpenShift Cluster Console

After the new instance boots and registers with the OpenShift cluster, it must be approved from the OpenShift console.

1. Log in to your **OpenShift Web Console** of your cluster.
2. Go to **Compute > Nodes**.
3. You new worker node should appear here.

<img src="files/16. NewWorker.png" width=400x align="top">

4. Click on the Discovered link and **Aprove** that the node is added to your cluster.

<img src="files/17. NewWorkerApprove.png" width=400x align="top">

5. As a final step you likely also need to approve the new nodes certificate. Click on the **Not Ready** link and approve the Certificate Signing process.

<img src="files/18. NewWorkerApprove2.png" width=400x align="top">

You node will now be accepted as a new worker node for your Openshift cluster and you will automatically start seeing pods running on this new node.
---

## Conclusion

Following this guide, you will successfully add a new host to your OpenShift cluster on Oracle Cloud Infrastructure (OCI). The new host will be automatically configured and integrated into the cluster after it is approved via the OpenShift web console.


# License
Copyright (c) 2024 Oracle and/or its affiliates.
Licensed under the Universal Permissive License (UPL), Version 1.0.
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
