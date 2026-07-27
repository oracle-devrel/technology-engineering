# How to enable custom logs in OCI Instances

One of the features of the logging service is the ability to collect logs directly from the running instance using the existing Oracle Cloud Agent. The only thing you need to do is to enable the Custom Agent Plug-in and create an Agent Configuration.

Custom Logs Diagnostic information from custom applications, other cloud providers, or an on-premise environment. To ingest custom logs, call the API directly or configure the unified monitoring agent.

Go to Menu → Observability&Management → Agent Configurations

![Picture 14](./files/image-01.png)

Click Create Agent config:

![Picture 13](./files/image-02.png)

![Picture 12](./files/image-03.png)

As you can see, there are 2 pre-requisites before the custom logs will work:

1- Configure the user group or Dynamic Group to use all instances from a compartment, or different instances to allow log collection

2- Create the Dynamic Group in Menu →Identity & Security → Dynamic Groups and press Create Dynamic Group

![Picture 11](./files/image-04.png)

Add the matching rule Following the Service documentation:

[Agent Management (oracle.com)](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/agent_management.htm)

An example is this:

![Picture 9](./files/image-05.png)

![Picture 8](./files/image-06.png)

Specify what you want to collect with the Agent

![Picture 7](./files/image-07.png)

If you want to monitor logs from files, you can also specify the location of the log.

![Picture 6](./files/image-08.png)

![Picture 5](./files/image-09.png)

Select the Log Group destination and press Create.

Ensure that Logging&Monitoring agent is enabled on the monitored hosts

![Picture 4](./files/image-10.png)

After a few minutes go to one instance where you have the Custom Logging enabled and check if the logs are there.

![Picture 3](./files/image-11.png)

You can also check the Logs in OCI Logging Service:

![Picture 2](./files/image-12.png)

![Picture 1](./files/image-13.png)

On my next blog entry, I will show you how to use the collected Windows logs with Logging Analytics to do a basic Threat Hunting.

Reviewed: 01.07.2026
