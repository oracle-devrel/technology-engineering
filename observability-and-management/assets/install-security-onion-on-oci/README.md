# How to install Security Onion on OCI

If you plan to create your own Security Operation Center using open-source solutions, one of the best Threat Detection and Monitoring, threat hunting, enterprise security monitoring, and log management is [Security Onion](https://securityonionsolutions.com/software/).

In this guide I will show you how to manually install Security Onion, and how to add an additional VNIC Adapter for VCN Traffic Capturing.

Install Ubuntu

Go to OCI →Menu →Compute →Instances and click Create Instance:

![Picture 31](./images/image-01.png)

Fill the fields, Select the compartment and Ad and select Ubuntu Shape:

![Picture 30](./images/image-02.png)

Select Ubuntu 20 from Browse all Images menu:

![Picture 29](./images/image-03.png)

Select the Shape you want to use ( Build it your self as you want) :

![Picture 28](./images/image-04.png)

Select the VCN and the subnet:

![Picture 27](./images/image-05.png)

Upload or generate the new ssh key for Ubuntu user:

![Picture 26](./images/image-06.png)

Increase the boot volume of the server, as you will need more then 50 GB on the long run for security monitoring and press create. Recommended is 250 to start, as Security Union is asking 200 GB on setup.

![Picture 25](./images/image-07.png)

After the Instance is created, click on the Attached VNICs and add the additional VNIC that will capture the network traffic.

![Picture 24](./images/image-08.png)

![Picture 23](./images/image-09.png)

Next step is to SSH to the newly created instance and start the Installation by running this commands:

sudo so-allow is used for opening the Security Onion Service ports.

![Picture 22](./images/image-10.png)

After the 2nd VNIC is added it will appear as ens5

```text
curl https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/secondary_vnic_all_configure.sh -O
chmod +x secondary_vnic_all_configure.sh
sudo ./secondary_vnic_all_configure.sh -c
```

![Picture 21](./images/image-11.png)

After running sudo bash so-setup-network command you will be redirected to Security Onion Install menu:

![Picture 20](./images/image-12.png)

Press Yes

Select Install Type and press OK. I have selected Evaluation mode.

![Picture 18](./images/image-13.png)

Type AGREE to Agree with the Elastic Stack Licensing.

![Picture 17](./images/image-14.png)

As I selected less space for the Boot Volume that the required space I got this error, but I continued the installation:

![Picture 16](./images/image-15.png)

Next you enter the hostname and press Ok:

![Picture 15](./images/image-16.png)

And you select Yes that the DNS and other prerequistes are configured.

![Picture 14](./images/image-17.png)

You accept the risk of DHCP IP Changing:

![Picture 13](./images/image-18.png)

You select ens3 as the management VNIC:

![Picture 12](./images/image-19.png)

Press OK on next step and select connection as Direct, if you don’t have a proxy in place:

![Picture 11](./images/image-20.png)

Wait for checks to be done:

![Picture 10](./images/image-21.png)

Select ens5 as the monitoring interface:

![Picture 9](./images/image-22.png)

Define your internal IP’s that are allowed to connect to your Security Onion Server and press OK:

![Picture 8](./images/image-23.png)

Install the Optional Services that you want to use and press Ok:

![Picture 7](./images/image-24.png)

Keep the Docker IP range and press OK:

![Picture 6](./images/image-25.png)

Create the management user and set the password:

![Picture 5](./images/image-26.png)

Specify how you like to access the instance:

![Picture 4](./images/image-27.png)

![Picture 3](./images/image-28.png)

Select the IP that is allowed to access the Security Onion. I selected all, as this is in a private subnet, and the instace will be destroyed after the demo.

![Picture 2](./images/image-29.png)

Press yes and wait for the installation to finish:

![Picture 1](./images/image-30.png)

Congratulations! You have a new Security Onion Instance running on OCI.

run the script to be sure the 2nd VNIC Is up and running properly:

```text
curl https://docs.oracle.com/en-us/iaas/Content/Resources/Assets/secondary_vnic_all_configure.sh -O
chmod +x secondary_vnic_all_configure.sh
sudo ./secondary_vnic_all_configure.sh -c
```
