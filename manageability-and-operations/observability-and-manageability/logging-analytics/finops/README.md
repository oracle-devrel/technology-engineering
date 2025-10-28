# Mastering Cloud Cost Control with OCI Log Analytics 

Oracle Cloud Infrastructure (OCI) provides several built-in tools to
help users monitor, analyze, and control cloud spending. Among these
tools are OCI Cost Analysis and Scheduled Reports, which offer
visibility into usage patterns and cost trends over time. These tools
are valuable for high-level reporting and day-to-day cost tracking,
especially when trying to stay within budget or identify cost anomalies.

However, for more in-depth analysis—such as breaking down spending
across departments, correlating costs with specific resource tags, or
building custom dashboards—access to raw cost and usage data becomes
essential. This is where the ability to export and analyze detailed cost
reports becomes particularly useful.

OCI is fully compliant with the FinOps Foundation’s FOCUS (FinOps Open
Cost and Usage Specification) standard. The FOCUS report provides a
standardized and comprehensive dataset that includes detailed
information about costs, services, compartments, tags, and more. This
standardized format makes it easier to integrate OCI cost data into
third-party tools or advanced analytics platforms.

In this article, I will walk you through the process of importing a
FOCUS report into OCI Log Analytics. By doing this, you can take
advantage of powerful querying capabilities and visualization features
within the Log Analytics platform. This approach allows you to build
customized dashboards, run advanced queries, and perform granular
analysis tailored to your organization’s specific needs.

Whether you're aiming to implement FinOps best practices, provide cost
transparency to internal stakeholders, or simply gain a better
understanding of your cloud expenses, integrating FOCUS data into Log
Analytics can help you unlock new levels of insight and control.

An example of a custom dashboard could include the ability to drill down
into specific compartments, offering a clear and detailed view of the
services being used and their associated consumption. This level of
insight enables teams to identify which services are contributing most
to overall costs, uncover underutilized or idle resources, and
understand usage trends over time. As a result, it becomes significantly
easier to make informed decisions that support cost optimization
strategies, improve budget forecasting, and ultimately lead to
meaningful cost savings across the organization.

<img src="./files/images/image1.png"
style="width:10.5in;height:1.93889in" />

Fig.1 – Compartment spending dashboard

Creating custom dashboards in OCI Log Analytics is extremely
straightforward, thanks to its flexible query and visualization
capabilities. You can tailor these dashboards to meet your specific
FinOps needs, whether you're tracking costs by compartment, service, or
tag.

You can set up specific alerts for example, for usage overages. These
alerts can trigger actions such as sending an email, reducing resource
limits, or even shutting down services.

<img src="./files/images/image2.png"
style="width:6.5in;height:0.82569in" />

Fig. 2 – Alert on overage

Additionally, the approach is not limited to Oracle Cloud—Log Analytics
can be extended to ingest data from other cloud providers as well. This
makes it possible to build a unified, cross-cloud FinOps dashboard that
consolidates cost and usage data from multiple environments into a
single, personalized view.

Ready to set it up in your own environment? Keep reading to learn how!

## Architecture

<img src="./files/images/image3.png"
style="width:6.5in;height:1.85347in" />

Fig. 3 - The architecture

Consumption information is reported in the FOCUS report, which resides
on the internal Oracle tenant.

Each day, a function retrieves this report and creates a copy in the
Cost\_Usage\_Report. As soon as the report is created, an event is
triggered, and the data is imported into Logging Analytics using a
specific FOCUS Log Source.

Once ingested, the data feeds into the FinOps dashboard and can
eventually trigger alerts.

These alerts use a specific Notification Channel, where the associated
action is defined. The action can be sending an email or triggering a
function to perform a custom remediation action.

*Create an Object Storage in your tenant*

In the OCI Console, under "Storage", click on "Object Storage" → then
"Buckets". Choose the compartment where you want to create the bucket.

> <img src="./files/images/image4.png"
> style="width:6.13127in;height:3.19521in" />

Fig 4 - Bucket creation

After you create it, note the bucket namespace, name, and URL—you’ll
need these for uploading or referencing objects via APIs, CLI, or
automation tools.

*Set up IAM policies*

Create a Dynamic Group for function and Log Analytics Object rule

Create a policy with the follow statement

dg-fn-copy-CUR-reports dynamic group matching rule
```
ALL {resource.type = 'fnfunc', resource.compartment.id = '&lt;finOps
compartment OCID&gt;’}
```
LogAnalyticsObjectCollectionRule dynamic group matching rule
```
ALL {resource.type='loganalyticsobjectcollectionrule',
resource.compartment.id = '&lt;finOps compartment OCID&gt;’}
```
Policy Statements
```
define tenancy usage-report as
ocid1.tenancy.oc1..aaaaaaaaned4fkpkisbwjlr56u7cj63lf3wffbilvqknstgtvzub7vhqkggq

endorse group finOps to read objects in tenancy usage-report

allow group finOps to manage analytics-instances in compartment
&lt;finOps compartment&gt;

allow service metering\_overlay to manage objects in compartment
&lt;finOps compartment&gt;

Allow group finOps to manage functions-family in compartment &lt;finOps
compartment&gt;

Allow group finOps to manage health-check-family in compartment
&lt;finOps compartment&gt;

Allow group finOps to manage virtual-network-family in compartment
&lt;finOps compartment&gt;

Allow dynamic-group dg-fn-copy-CUR-reports to manage objects in
compartment &lt;finOps compartment&gt;

endorse dynamic-group dg-fn-copy-CUR-reports to read objects in tenancy
usage-report

Allow dynamic-group dg-fn-copy-CUR-reports to inspect compartments in
tenancy

Allow dynamic-group dg-fn-copy-CUR-reports to inspect tenancies in
tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to read buckets in
tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to read objects in
tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to manage
cloudevents-rules in tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to inspect
compartments in tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to use
tag-namespaces in tenancy

allow DYNAMIC-GROUP LogAnalyticsObjectCollectionRule to
{STREAM\_CONSUME} in tenancy
```
*Create the Functions to export the Report into a custom Object Storage*

Create an application in OCI Console. Go to Developer Services &gt;
Applications &gt; Create Application &gt; FinOpsX86

<img src="./files/images/image5.png"
style="width:5.27588in;height:3.3402in" />

Fig.5 – Application

In OCI Shell initialize the function:
```
fn init --runtime python copyusagereport

cd copyusagereport
```
Go to OCI Shell and edit the func.py
```
import io

import json

import logging

import oci

from datetime import datetime, timedelta

from fdk import response

def handler(ctx, data: io.BytesIO = None):

try:

reporting\_namespace = 'bling'

reporting\_bucket = '<Tenancy OCID>'

yesterday = datetime.now() - timedelta(days=3)

prefix\_file = f"FOCUS
Reports/{yesterday.year}/{yesterday.strftime('%m')}/{yesterday.strftime('%d')}"

print(f"prefix is {prefix\_file}")

destination\_path = '/tmp'

dest\_namespace='frxfz3gch4zb'

upload\_bucket\_name = 'Cost\_Usage\_Reports'

Signer = oci.auth.signers.get\_resource\_principals\_signer()

object\_storage = oci.object\_storage.ObjectStorageClient(config={},
signer=Signer)

report\_bucket\_objects =
oci.pagination.list\_call\_get\_all\_results(object\_storage.list\_objects,
reporting\_namespace, reporting\_bucket, prefix=prefix\_file)

for o in report\_bucket\_objects.data.objects:

object\_details = object\_storage.get\_object(reporting\_namespace,
reporting\_bucket, o.name)

filename = o.name.rsplit('/', 1)\[-1\]

local\_file\_path = destination\_path+'/'+filename

with open(local\_file\_path, 'wb') as f:

for chunk in object\_details.data.raw.stream(1024 \* 1024,
decode\_content=False):

f.write(chunk)

with open(local\_file\_path, 'rb') as file\_content:

object\_storage.put\_object(

namespace\_name=dest\_namespace,

bucket\_name=upload\_bucket\_name,

object\_name=filename,

put\_object\_body=file\_content

)

except (Exception, ValueError) as ex:

logging.getLogger().info('error parsing payload: ' + str(ex))

return response.Response(

ctx, response\_data=json.dumps(

{"message": "Processed Files sucessfully"})

)
```
Deploy the function
```
fn -v deploy --app FinOpsX86
```
Define a scheduler. Create an application in OCI Console. Go to
Developer Services &gt; Applications &gt; Create Application &gt;
FinOpsX86&gt; copyusagereport &gt; Schedules &gt; Add Schedule

<img src="./files/images/image6.png"
style="width:3.94444in;height:4.23611in" />

Fig.6 – Funcion Schedule 

*Create a Log Group on Log Analytics*

> Go to **Observability & Management** → **Log Analytics** →
> **Administration** → **Log Groups**. Select the **compartment** where
> you want to create the log group from the left-side menu.
>
> <img src="./files/images/image7.png"
> style="width:4.69444in;height:2.10278in" />
>
Fig.7 – Log Group

OCI Create Log Group
>
> Click the **“Create Log Group”** button.

Top of Form

Bottom of Form

*Import the FOCUS parser and Source*

> Download the Source configuration from [here](./files/src/FOCUS_OCI_1760704183250.zip).
>
> Go to **Observability & Management** → **Log Analytics** →
> **Administration** → **Import Configuration Content** and select the
> file you have just downloaded.
>
> <img src="./files/images/image8.png"
> style="width:3.47989in;height:3.03434in" />

Create the Streaming

> Streaming is required to upload newly created items in the bucket to
> Log Analytics. Data will be injected every time a new item is created.
>
> The injection frequency depends on the schedule configured in the
> previous step. In this case, the frequency is every 24 hours.

Go to **Analytics & AI** → **Streaming** → **Stream Pools**→ **Create
Stream Pool**.

> <img src="./files/images/image9.png"
> style="width:3.08333in;height:5.22222in" />

*Create the Object Rule on Log Analytics*

From OCI Shell console create the json file
```
{

"name": "FocusObjectRule",

"compartmentId":
"<Compartment OCID>",

"osNamespace": "frxfz3gch4zb",

"osBucketName": "Cost\_Usage\_Reports",

"logGroupId":
"<LogGroup OCID>",

"logSourceName": "FOCUS\_OCI",

"streamId":"<Stream OCID>"

}
```
Run
```
oci log-analytics object-collection-rule create --from-json
file://createFocusObjectRule.json --namespace-name frxfz3gch4zb
```
*Import the FOCUS Dashboard*

> Download the dashboard configuration from [here](./files/src/FinOps_final.json).
>
> Go to **Observability & Management** → **Management Dashboards** **→
> Import dashboards** and select the file you have just downloaded.
>
> <img src="./files/images/image10.png"
> style="width:6.5in;height:1.88958in" />

*Create the alert*

> You can create a specific alert by defining metrics with a detection
> rule. Once the metric is created, you can configure an alert based on
> it.
>
> For example, I created an alert for *Overage*. An overage occurs when
> a customer exceeds the budget they have committed to.
>
> Go to **Observability & Management → Log Analytics → Administration →
> Detection Rules → Create**
>
> In the Metric Namespace, you can choose a custom name, as well as
> define the metric name. Be sure to run the recommended Dynamic Group
> policies.
>
> I used FO\_Total\_Overage but you can use all other FinOps Dashboard
> widget or create new ones.
>
> <img src="./files/images/image11.png"
> style="width:6.5in;height:2.69861in" />
>
> <img src="./files/images/image12.png"
> style="width:6.5in;height:2.51597in" />
>
> Wait 24 hours for the data to be imported and for the
> metric\_namespace to be populated. After that, you can define a
> specific alert.
>
> Go to **Observability & Management → Monitoring → Alarm Definitions →
> Create Alarm**
>
> <img src="./files/images/image13.png"
> style="width:6.5in;height:3.11875in" />
>
> By integrating the OCI FOCUS cost and usage report into Log Analytics,
> you've unlocked a powerful, flexible, and scalable approach to cloud
> cost visibility and optimization. This solution not only aligns with
> FinOps best practices, but also empowers you to build custom
> dashboards, set intelligent alerts, and automate responses to budget
> anomalies all within a single OCI-native environment.
>
> The FOCUS report format is also supported by other cloud vendors. If
> you wish, you can import FinOps reports from other providers by
> uploading them to the same Object Storage bucket. This enables a
> unified, cross-cloud view of your cloud spending and usage patterns
> within OCI Log Analytics.
>
> Whether your goal is to improve forecasting, drive accountability, or
> reduce unnecessary spending, this setup provides the insights and
> control needed to act. With extensibility to multi-cloud environments,
> your FinOps strategy can grow seamlessly alongside your cloud
> footprint.
>
> Now that the infrastructure is in place—from scheduled report
> ingestion to alerting and dashboarding—you can continuously refine
> your analytics, extend with additional data sources, or tailor your
> metrics to evolving business goals.
>
> With this foundation, you're well-equipped to transform raw cost data
> into strategic, actionable insight—and make FinOps a central pillar of
> your cloud operations.
