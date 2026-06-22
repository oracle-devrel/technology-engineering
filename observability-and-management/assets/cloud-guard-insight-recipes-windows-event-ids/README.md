# Use Cloud Guard Insight Recipes to monitor Windows Instances against Interesting Windows Event IDs for Malware-General Investigation

Recently Oracle lunched a new Recipe called Insight. With this service you will be able to leverage the OCI logging service Search Options and also the advanced Threat detection Engine from Cloud Guard.

[Getting Started with Data Sources (oracle.com)](https://docs.oracle.com/en-us/iaas/cloud-guard/using/datasrc-start.htm)

In this blog entry I will try to showcase how easy is to create a Data Source and a Recipe based on the Saved Log Searches/New Searches.

The Event ID’s that I will add in this Search are from this Sophos page, and the ID’s are found in the Windows events if the instances are compromised.

[Interesting Windows Event IDs — Malware/General Investigation (sophos.com)](https://support.sophos.com/support/s/article/KB-000038860?language=en_US)

So the first thing we need to do is to create the OCI AuthZ policies that will allow the Logging Service to be used by Cloud Guard.

Go to Cloud Guard, click on Data Sources and copy the needed policies:
```test
allow service logging to {LOG_DEFINITION_READ, LOG_DEFINITION_WRITE, LOG_WRITE, LOG_NAMESPACE_READ, LOG_CONTENT_READ, AUDIT_EVENT_READ,LOG_CONTENT_PUSH} in tenancy
```
allow service logging to {INTERNAL_AUDIT_EVENT_READ} in tenancy

![Picture 36](./images/image-01.png)

The policy needs to be enabled at the root level.

![Picture 35](./images/image-02.png)

Next step would be to go to OCI Logging, and create a Search for certain event ID from a Custom Agent Log for Windows.

```text
search “ocid1.compartment.oc1..xxx/ocid1.loggroup.oc1.eu-frankfurt-1.xxxx/ocid1.log.oc1.eu-frankfurt-1.xxx”| data.event_id=’7036' or data.event_id=’4688' or data.event_id=’4740'| sort by datetime desc
```
![Picture 34](./images/image-03.png)

You can press Save Search, and this search can be choose when you create the rule. If you don’t want to save the search, you can also copy and paste.

After you have the proper search for your events of interest, you can go to Cloud Guard and Press Create Query:

![Picture 33](./images/image-04.png)

\

After you select the Region, give query a name, you can click Import Saved Search Query

![Picture 32](./images/image-05.png)

Based on how often you want to have the problems created you can change the trigger from 24h to once per hour or once at 5 minutes for testing.

![Picture 31](./images/image-06.png)

![Picture 30](./images/image-07.png)

And press import:

![Picture 29](./images/image-08.png)

After the Query is imported, you need to define the keys used by the query and mapping with Logging as seen below on the code:

![Picture 28](./images/image-09.png)

```text
search “ocid1.compartment.oc1..xxx/ocid1.loggroup.oc1.eu-frankfurt-1.xxx/ocid1.log.oc1.eu-frankfurt-1.xxx” | data.event_id=’7036' or data.event_id=’4688'or data.event_id=’4740' or data.event_id=’4648'| select data.event_id as cgkey01
```

If mapping is not done, you will receive this error:

![Picture 27](./images/image-10.png)

Now with the first query created, we can go with the Recipe creation. Go to Cloud Guard → Detector recipes → Create recipes

![Picture 26](./images/image-11.png)

![Picture 25](./images/image-12.png)

After the Recipe is created, we can go and add the rules by clicking on Create rule:

![Picture 24](./images/image-13.png)

![Picture 23](./images/image-14.png)

After the rule is added and Enabled, you can see how the log entity is mapped with the Cloud Guard Entity.

![Picture 22](./images/image-15.png)

After you have added the rule, you need to wait for new Events to be generated on your Windows Machine and a new Problem will be created in the Cloud Guard Problems page:

![Picture 21](./images/image-16.png)

Other Method to check for the events is by Clicking the Data Source and Click Events under Resource:

![Picture 20](./images/image-17.png)

Once the data source is added to the Rule, you will not be able to update the rule. As the events I have added initially are not generated all the time, I needed to add an additional login eventID.

Go to the Data Source:

![Picture 18](./images/image-18.png)

Click on Data Source and detach it from the Recipe

![Picture 17](./images/image-19.png)

![Picture 16](./images/image-20.png)

After you detach it, you can edit it and add additional EventID’s like 4672 , save the new search and create a new rule back in the Detection Insight Policy:

![Picture 15](./images/image-21.png)

![Picture 14](./images/image-22.png)

![Picture 13](./images/image-23.png)

```test
search “ocid1.compartment.oc1..xxx/ocid1.loggroup.oc1.eu-frankfurt-1.xxx/ocid1.log.oc1.eu-frankfurt-1.xxx” | data.event_id=’7036' or data.event_id=’4688'or data.event_id=’4740' or data.event_id=’4648' or data.event_id=’4740' | select data.event_id as xxx
```

Last step now is to attach Rule to the needed compartment by clicking Cloud Guard → Targets and create new Target:

![Picture 12](./images/image-24.png)

![Picture 11](./images/image-25.png)

Attach the mandatory policies and wait for the Events to be generated in the Cloud Guard.

![Picture 10](./images/image-26.png)

![Picture 9](./images/image-27.png)

![Picture 8](./images/image-28.png)

Congratulation! Now you can create proper Monitoring rules for Threat Hunting and Security Event Notifications.

Note: When you update an existing Data Source, there is a slight delay in updating the Data Source and the state will be Updating for a few minutes.

![Picture 7](./images/image-29.png)
