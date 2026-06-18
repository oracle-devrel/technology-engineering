# How to enable OCI Observability on Golden Gate Cloud

Oracle Cloud Infrastructure GoldenGate is a fully managed, native cloud service that moves data in real-time, at scale. OCI GoldenGate processes data as it moves from one or more data management systems to target databases.

![Picture 19](./images/image-01.png)

### Enable Logging Analytics

OCI services produces logs that are collecting into Logging Service. Logs will be tranfered into logging Analytics to provide advanced funcionalities

1. Enable Logging for OCI Golden Gate. Go on Observability and Management — > Logging →Logs →Enable Service Log

![Picture 18](./images/image-02.png)




2. Tranfer the GG logs to Logging analytics. Go on Observability and Management → Logging → Logs → Connectors → Create connector



![Picture 17](./images/image-03.png)



![Picture 16](./images/image-04.png)

3. Wait 5 minutes and then go on Observability and Management → Logging Analytics → Explorer



![Picture 15](./images/image-05.png)

4. Select OCI GoldenGate Process and Error.



![Picture 14](./images/image-06.png)

Now you can use all Logging Analytics capabilities.

### Enable Stack Monitoring

Enabling Stack Monitoring you will get Golden Gate Out of the Box dashbaord and[ extra metrics](https://docs.oracle.com/en-us/iaas/stack-monitoring/doc/metric-reference.html).

1. Install Management Agent on a OCI VM. Please refer to [this ](https://blogs.oracle.com/observability/post/oci-logginganalytics-compute-instance)Blog

2. Download Golden Gate certificate and save it on a location accessible by the Management Agent

Go on Golden Gate -> Deployments -> Launch console



![Picture 12](./images/image-07.png)

Download the certificate. Go on Connection is Secure →Certificate is valid → Details → Select the certificate →Export

![Picture 11](./images/image-08.png)

![Picture 10](./images/image-09.png)

![Picture 9](./images/image-10.png)

3. Copy the certificate on the Compute VM /tmp folder. Rename it as DigiCertGGConsole.crt and create the eystore on the Compute VM. Keystore location needs to be accesible by the agent

```text
sudo -u mgmt_agent sh
cd --
mv /tmp/DigiCert\ Global\ G2\ TLS\ RSA\ SHA256\ 2020\ CA1.crt DigiCertGGConsole.crt
keytool -import -file DigiCertGGConsole.crt -alias DigicertCA -keystore mgmt_agent_keystore
```

4. Discovery Golden Gate service. Go on Observability →Stack Monitoring →Resource Discovery →Discovery New resource

```text
Hostname = deployment console URL
Management Agent = Agent Name discovered in Observability -> Management Agent Console
TrustStore = /usr/share/mgmt_agent/mgmt_agent_keystore
```

Press enter or click to view image in full size

![Picture 8](./images/image-11.png)

![Picture 7](./images/image-12.png)

Press enter or click to view image in full size

![Picture 6](./images/image-13.png)

Press enter or click to view image in full size

![Picture 5](./images/image-14.png)

5. After the discovery process completed you can see Golden Gate in Stack Monitor console


![Picture 4](./images/image-15.png)



![Picture 3](./images/image-16.png)



![Picture 2](./images/image-17.png)



![Picture 1](./images/image-18.png)

Now you can use full Observability capability on your Golden Gate service.
