# Setting up a free TLS certificate for testing HTTPS connections on OCI Load Balancer

Owner: Paul Toal

Within OCI, the [Load Balancer Service](https://docs.oracle.com/en-us/iaas/Content/Balance/Concepts/balanceoverview.htm) enables you to create resilient connections to backend resources such as web servers.

Sometimes when you are testing backend services it is necessary to use a HTTPS connection. Normally, TLS certificates are issued against fully qualified domain names. However, it isn't always possible or quick and easy to register your testing resources with a domain.

In this tutorial, I will walk you through the process of quickly enabling HTTPS connection through the OCI load balancer, using a free TLS certificate generated by [ZeroSSL](https://app.zerossl.com/dashboard), and generated against an IP address.

## Prerequisites

 - An OCI tenancy.
 - An OCI Administrator with appropriate permissions to create and manage load balancers and associated resources.
 - Created a sample web site deployed on OCI. 
 
 > **Note** For this tutorial, I have created a compute instance called **apache** and installed and configured the Apache HTTPD service on it, running on port 80.

# Create the Load Balancer

Initially, we will create the load balancer and configure the HTTP listener on port 80. This will enable us to obtain the public IP address of the load balancer, which we will need to create the IP address-based TLS certificate. 

> **Note** If you are planning on using a reserved IP address and already know the public IP address, you can skip the creation of the HTTP listener and configure the HTTPS listener from the start.

1. Login to your OCI console and navigate to **Networking**, then **Load Balancer** from the **Load Balancers** menu.

2. Select the appropriate compartment and click `Create Load Balancer`.

3. In the **Add details** screen, provide the following information:

   - Load balancer name: `lb-for-apache`

   Leave the following values as their defaults:

   - Choose visibility type: `Public`
   - Assign a public IP address: `Ephemeral IP address`
   - Choose the minimum bandwidth: `10`
   - Choose the maximum bandwidth: `10`
   - Choose networking 
      -> VCN: Choose your VCN
      -> Subnet: Choose your public subnet

4. Leave all other values as default and click `Next'.

5. On the **Choose backends** screen, click `Add backends`.

6. Select the checkbox next to your compute instance (in my case `apache`) from the list of instances.

![Screenshot for selecting the backend.](images/lb-select-backend.png "Screenshot for selecting the backend.")

7. Click `Add selected backends`.

8. Leave the port for your backend as port 80.

9. Leave the health check policy as default.

10. Click `Next`.

11. On the **Configure listener** screen, provide the following information:

   - Name: `listener-http`
   - Specify the type of traffic your listener handles: `HTTP`
   - Specify the port your listener monitors for ingress traffic: `80`

12. Click `Next`.

13. Since, this is a test, disable **Error logs** and **Access Logs** (if enabled).

![Screenshot for load balancer logging.](images/lb-logging.png "Screenshot for load balancer logging.")

14. Click `Submit`.

Your load balancer will be created after a few moments.

![Screenshot for load balancer summary.](images/lb-created.png "Screenshot for load balancer summary.")

> **Note** If you have enabled the network traffic to your HTTPD server, and if it is running, **Backend sets health** shoudl be showing as **OK**. If not, check your networking and security lists.

15. Make a note of the public IP address of your load balancer.

# Test the Load Balancer

Before we enable a HTTPS connection to the web server, let's check out load balancer is working and routing traffic correctly.

1. Open a browser and navigate to `http://<your LB public IP address>/`, accepting the HTTP warning issued by your browser.

![Screenshot for HTTP web site access.](images/browser-http.png "Screenshot for HTTP web site access.")

# Generate the TLS certificate

Now that we have our load balancer listening on HTTP with a public IP address, we can generate an IP-based TLS certificate.

For this tutorial, i'm using [ZeroSSL](https://app.zerossl.com/dashboard), primarily because they offer the ability to generate up to three, 90-day certificates for free, and will generate certificates based on IP addresses, not just domain names.

1. Navigate to `https://app.zerossl.com/dashboard`.

2. If you don't already have one, register for a free account and login.

3. Click on `New Certificate` to start the certificate generation wizard.

4. Enter the IP address of your load balancer in the **Domain Name** field.

The IP will be validated as shown by the green tick.

![Screenshot for entering IP on ZeroSSL new certificate screen.](images/zerossl-ip.png "Screenshot for entering IP on ZeroSSL new certificate screen.")

5. Click **Next Step ->**

4. Under **Validity**, select `90-Day Certificate`.

![Screenshot for entering validity on ZeroSSL new certificate screen.](images/zerossl-validity.png "Screenshot for entering validity on ZeroSSL new certificate screen.")

5. Click **Next Step ->**

6. Don't select any add-ons. 

![Screenshot for entering add-ons on ZeroSSL new certificate screen.](images/zerossl-addons.png "Screenshot for entering add-ons on ZeroSSL new certificate screen.")

7. Click  **Next Step ->**

8. On the **CSR & Contact** screen, ensure `Auto-Generate CSR` is enabled.

![Screenshot for entering CSR on ZeroSSL new certificate screen.](images/zerossl-CSR.png "Screenshot for entering CSR on ZeroSSL new certificate screen.")

9. Click **Next Step ->**

10. Under **Finalize Your Order**, leave `Free` selected.

![Screenshot for entering order on ZeroSSL new certificate screen.](zerossl-freeorder.png "Screenshot for entering order on ZeroSSL new certificate screen.")

11. Click **Next Step ->**

Before ZeroSSL will issue a certificate, you must verify that you control the IP address that you have requested a certificate for. Since this is a free, 90-day certificate, the only method of validation is to upload a temporary file to your web server.

12. Follow the instructions to upload the pki-validation file to your web server into the folder specified by ZeroSSL.

![Screenshot for verifying IP address.](images/zerossl-verify.png "Screenshot for verifying IP address.")

13. Once the file is in place, click **Verify Domain** to start the verification process.

After successful verification, your certificate will be generated.

14. Click **Download Certificate (.zip)** to obtain the necessary certificate and key files from ZeroSSL.

![Screenshot for ZerosSSL certificate download.](images/zerossl-download.png "Screenshot for ZerosSSL certificate download.")

15. Extract the zip file to a suitable folder on your local machine. It contains three files:

 - **certificate.crt** - is the actual X.509 certificate
 - **ca_bundle.crt** - is the signing certificate
 - **private.key** - is the private key for your certificate

 We will need all three in the next step.

# Create the HTTPS listener

Now that we have our 90-day TLS certificate from ZeroSSL, we can create a HTTPS listener on our load balancer.

1. Back in the OCI console, navigate back to your load balancer at **Networking**, then **Load Balancer** from the **Load Balancers** menu.

2. Select your **lb-for-apache** load balancer.

Before creating the HTTPS listener, we need to import our new certificate.

3. From the **Resources** left-hand menu, select **Certificates**.

4. Change the **Certificate Resources** to `Load balancer managed certificate`.

![Screenshot for certificate selection.](images/lb-cert-list.png "Screenshot for certificate selection.")

5. Click **Add certificate**.

6. Provide a name for your certificate such as its IP address.

![Screenshot for certificate name.](images/cert-name.png "Screenshot for certificate name.")

7. Under **Choose SSL certificate file**, drop your `certificate.crt` file into the box.

![Screenshot for certificate file.](images/cert-cert.png "Screenshot for certificate file.")

8. Check the **Specify CA certificate** check box.

9. Under **Choose CA certificate file**, drop your `ca_bundle.crt` file into the box.

![Screenshot for CA certificate file.](images/cert-ca.png "Screenshot for certificate file.")

8. Check the **Specify private key** check box.

9. Under **Choose CA private key file**, drop your `private.key` file into the box.

![Screenshot for private key file.](images/cert-priv.png "Screenshot for private key file.")

10. Click **Add certificate** to to finalise the addition of the certificate.

11. Click **Close** on the **Work Request** and wait for the new certificat to appear in the list of certificates (a new moments).

![Screenshot for imported cert.](images/cert-list.png "Screenshot for imported cert.")

Now that we have our certificate imported, we can create the new listener.

12. From the **Resources** left-hand menu, select **Listeners**.

13. Click **Create listener**.

14. Provide following values on the **Create listener screen:

   - Name: `listener-https`
   - Protocol: `HTTPS`
   - Port: `443`
   - Use SSL: Checked
   - SSL certificate
      - Certificate resource: `Load balancer managed certificate`
      - Certificate name: `<your LB public IP address>` (or the name you specified in step 6 above)
   - Backend set: Select your backend set from the dropdown list

15. Click **Create listener**.

16. Click **Close** on the **Work request submitted** screen and wait for the new listener to appear.

# Testing our new listener

Now that we have created the HTTPS listener, we can test it.

1. Open a browser and navigate to `https://<your LB public IP address>/`.

You will see that you now have a secure connection to your web server, as indicated by the padlock in your browser address bar.

![Secure browser connection to web site.](images/browser-https.png "Secure browser connection to web site.")

This completes the lab.

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.