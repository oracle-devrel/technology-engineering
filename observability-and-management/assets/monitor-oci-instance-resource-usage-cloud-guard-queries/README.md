# How to monitor the resource usage on your OCI Instances using Cloud Guard Instance Security Queries

Oracle Cloud Guard’s Instance Security feature is a powerful tool designed to enhance your cloud security posture by continuously monitoring, identifying, and responding to potential risks in your Oracle Cloud Infrastructure (OCI) instances. Now, even if it’s main task is Security, you can extend the usage of this service to Observability, and run advanced queries.

One of the usecases I was asked about is how to monitor the usage of resources on a OCI instance, and I tested and proposed this workflow.

Behind the Queries is OSQuery, a very powerful tool that can be used to run SQL like queries against the OS.

Cloud Guard allows you to create and customize (security/observability) queries based on your specific operational needs. Whether you need to track unauthorized access, ensure compliance, or monitor resource usage, Instance Security Queries(Paid feature) provide the flexibility to build targeted checks tailored to your organization’s security requirements.

For this blog entry I will focus on Process and Resource Monitoring.

By using OSQuery integrated with Cloud Guard, you can monitor processes running on your instances, identify suspicious activities, and track resource utilization. This level of monitoring helps in early detection of anomalies, such as unauthorized users or unexpected resource consumption spikes.

1 — Enable Cloud Guard(It’s free to monitor your OCI tenancy!!!) if you haven’t in your tenancy and create the proper IAM rules:

Prerequisites | [Link](https://docs.oracle.com/en-us/iaas/cloud-guard/using/prerequisites.htm?source=post_page-----342836ca2811---------------------------------------)


2- Get familiar with the Query service capabilities:

About Queries | [Link](https://docs.oracle.com/en-us/iaas/cloud-guard/using/queries-about.htm?source=post_page-----342836ca2811---------------------------------------)



3- Go to Cloud Guard →Configuration →Create new target → Point it to your compartment:

![Picture 34](./images/image-01.png)

![Picture 33](./images/image-02.png)

Select the recieps:

![Picture 32](./images/image-03.png)

I have attached all this receips and saved:

![Picture 31](./images/image-04.png)

Check the Instance to have Cloud Guard Workload Protection(Paid feature) enabled.

![Picture 30](./images/image-05.png)

4- Go to Cloud Guard → Queries and run the needed queries

![Picture 29](./images/image-06.png)

Some examples:

```text
— Provide an osquery
SELECT
 u.username AS user,
 g.groupname AS `group`,
 COUNT(p.pid) AS process_count,
 SUM(p.user_time + p.system_time) AS total_cpu_time,
 ROUND((SUM(p.user_time + p.system_time) / (SELECT SUM(user_time + system_time) FROM processes)) * 100, 2) AS cpu_usage_percentage,
 SUM(p.resident_size) AS total_memory_usage,
 ROUND((SUM(p.resident_size) / (SELECT SUM(resident_size) FROM processes)) * 100, 2) AS memory_usage_percentage
FROM
 processes p
JOIN
 users u ON p.uid = u.uid
JOIN
 groups g ON u.gid = g.gid
GROUP BY
 u.username, g.groupname
ORDER BY
 cpu_usage_percentage DESC, memory_usage_percentage DESC
LIMIT 10;
```

![Picture 28](./images/image-07.png)

Now we have the results, we can get this data and use it for additional computations. At this point I will download the CSV with the results, but you can also use the OCI logging to collect this queries as Query Results(WIP to enable it):

![Picture 27](./images/image-08.png)

You need to go to Past Queries and click Download results(csv format)

![Picture 26](./images/image-09.png)

Extract the file:

![Picture 25](./images/image-10.png)

Go to Logging Analytics →Administration →Click Upload Files:

![Picture 24](./images/image-11.png)

![Picture 23](./images/image-12.png)

![Picture 22](./images/image-13.png)

At this point I see I don’t have a valid Source for this, so I need to create it:

![Picture 21](./images/image-14.png)

Before this, I also need a parser for this file(Create XML Type → Copy paste the file content to ):

![Picture 20](./images/image-15.png)

![Picture 19](./images/image-16.png)

![Picture 18](./images/image-17.png)

Now map the fields and create new fields.

![Picture 17](./images/image-18.png)

After mapping run a parser test:

![Picture 16](./images/image-19.png)

Click on the ! sign and change the parser to the right format.

![Picture 15](./images/image-20.png)

![Picture 14](./images/image-21.png)

Based on the OSQuery created, you can have different fields. In my case I had this ones created as STRING.

![Picture 13](./images/image-22.png)

Next create the source with the new parser:

![Picture 12](./images/image-23.png)

![Picture 11](./images/image-24.png)

With the source created, we can restart the file upload wizard:

![Picture 10](./images/image-25.png)

Next we can see the OSQuery in the Log Explorer, and we can start playing with the numbers:

![Picture 9](./images/image-26.png)

```text
‘Log Source’ = OSQuery | fields ‘CPU Usage (%)’, ‘Process CPU Time’, ‘Action User’, ‘OS Process ID’ | timestats count as logrecords by ‘Log Source’ | sort -logrecords
```

Based on your usecase you can monitor the user/groups.

![Picture 8](./images/image-27.png)

![Picture 7](./images/image-28.png)

Now with the logs in Logging Analytics sky is the limit. One use case is to map the usage per groups:

![Picture 6](./images/image-29.png)

```text
‘Log Source’ = OSQuery | where result.total_memory_usage != ‘null’ | eval clean_memory_usage = replace(result.total_memory_usage, ‘“‘, ‘’) | eval numeric_memory_usage = toNumber(clean_memory_usage) | stats sum(numeric_memory_usage) as total_memory_usage_sum by Group
```

If you want to use see in MB, you can use another query like this:

```text
‘Log Source’ = OSQuery | where result.total_memory_usage != ‘null’ | eval clean_memory_usage = replace(result.total_memory_usage, ‘“‘, ‘’) | eval numeric_memory_usage = toNumber(clean_memory_usage) / 1000000 | stats sum(numeric_memory_usage) as total_memory_usage_sum_MB by Group
```

![Picture 5](./images/image-30.png)

For CPU Usage you can try something like this:

![Picture 4](./images/image-31.png)

```text
‘Log Source’ = OSQuery | where result.total_cpu_time != ‘null’ | eval clean_CPU_usage = replace(result.total_cpu_time, ‘“‘, ‘’) | eval numeric_CPU_usage = toNumber(clean_CPU_usage) | eval cost_rate_per_second = 0.001 | eval total_cost = numeric_CPU_usage * cost_rate_per_second | stats sum(total_cost) as total_CPU_cost_sum by Group
```

[https://docs.oracle.com/en-us/iaas/logging-analytics/doc/use-timestats-command-plot-time-series.html](https://docs.oracle.com/en-us/iaas/logging-analytics/doc/use-timestats-command-plot-time-series.html) — Some Dashboard capabilities ideas.

This are some highlights on the service capabilities. This capabilities can be entended to multiple OS behavior/monitoring use cases. You need to do the mapping based on the data format you ingest.

This is my personal opionion, and use it only if it fits your needs.

Preview of Part 2 — Adding automation:

1. Create a Scheduled Query

![Picture 3](./images/image-32.png)

1. Create and enable logging for it

![Picture 2](./images/image-33.png)

![Picture 1](./images/image-34.png)

1. Send the Logs to Logging Analytics

2. Create queries on collected data.
