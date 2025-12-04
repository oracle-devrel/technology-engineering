<!--
Copyright (c) 2025 Oracle and/or its affiliates.

The Universal Permissive License (UPL), Version 1.0

Subject to the condition set forth below, permission is hereby granted to any
person obtaining a copy of this software, associated documentation and/or data
(collectively the "Software"), free of charge and under any and all copyright
rights in the Software, and any and all patent rights owned or freely
licensable by each licensor hereunder covering either (i) the unmodified
Software as contributed to or provided by such licensor, or (ii) the Larger
Works (as defined below), to deal in both

(a) the Software, and
(b) any piece of software and/or hardware listed in the lrgrwrks.txt file if
one is included with the Software (each a "Larger Work" to which the Software
is contributed by such licensors),

without restriction, including without limitation the rights to copy, create
derivative works of, display, perform, and distribute the Software and make,
use, sell, offer for sale, import, export, have made, and have sold the
Software and the Larger Work(s), and to sublicense the foregoing rights on
either these or other terms.

This license is subject to the following condition:
The above copyright notice and either this complete permission notice or at
a minimum a reference to the UPL must be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
-->

# OCI Container Instances Grafana and Prometheus example with Java Sprinboot
## With multiple volumes and a custom sidecar to tail access log to OCI Logging and mount the Grafana and Prometheus configs from OCI Object Storage bucket for live changes  

Reviewed: 4.12.2025
 
## When to use this asset?
 
Anyone who wants to experiment with OCI Container Instances and setup a multi-container instance with multiple volumes and have a setup for Prometheus and Grafana. Including:

<ul>
<li>Node exporter for the OCI container instance metrics</li>
<li>Spring Boot Java exporter for app metrics</li>
<li>Logs are exported to OCI Logging with a custom sidecar. Springboot app log is configured to <code>resources/application.properties</code> as <code>/var/log/app.log</code></li>
<li>Custom sidecar also pulls configs in 30s intervals from a Object Storage private bucket for easy config changes to <code>/etc</code> of Prometheus and Grafana containers' shared volume</li>
</ul>

## Author
<a href="https://github.com/mikarinneoracle">mikarinneoracle</a>

## How to use this asset?

## Build containers

Build containers with GitHub Actions <code>containers.yml</code>pipeline
<p>
    
This requires three secrets:
<pre>
DOCKER_USERNAME
AUTH_TOKEN
TENANCY_NAMESPACE
</pre>

It uses <code>FRA</code> region for OCIR, i.e. Registry is <code>fra.ocir.io</code>

## Create object storage bucket with Prometheus and Grafana configs

Bucket name: <code>prometheus-grafana</code> (default, can be changed when deploying the Stack)
<p>
Directories in the bucket:
<pre>
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       └── datasources/
└── prometheus/
</pre>
Upload files from <code>object-storage</code> to the directory structure above in the bucket.
<p>
<b>Note!</b> Remember to change the <code>username</code> and <code>password</code> in <code>grafana.ini</code> before uploading!

## Deploy the Container Instances with the Terraform Stack

Deploy the Container Instances stack with OCI Resource Manager (Terraform). First clone this repo to localhost and drag-drop the terraform folder to OCI Resource Manager to create a new Stack. Then configure the stack and apply.
<p>
    
Subnet ports can be opened for the following access:
<ul>
    <li>8080 for the Springboot app</li>
    <li>3000 for Grafana</li>
    <li>9090 for Prometheus (optional)</li>
</ul>
<p>
    
For taking this to a a quick spin, you can create/use a VCN with a public subnet to have public access to Grafana.
VCN and subnet creation including the ports above is manual and not included in the Terraform Stack.
<p>

Also the OCI Log needs to be created manually for logging.
<p>

Once created git clone this repo and drag&drop the terraform folder to OCI Resource Manager when creating a new Stack.
Then, configure the stack vars and apply to have the stack deployed for testing. Destroy and delete after finishing the test.


## Useful Links
 
- [OCI Container Instances](https://www.oracle.com/cloud/cloud-native/container-instances/)
    - Learn how OCI Container Instances lets you easily run applications on serverless compute optimized for containers
- [OCI SDK](https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdks.htm)
    - Oracle Cloud Infrastructure provides a number of Software Development Kits (SDKs) and a Command Line Interface (CLI) to facilitate development of custom solutions
- [OCI Logging](https://docs.oracle.com/en-us/iaas/Content/Logging/Concepts/loggingoverview.htm)
    - The Oracle Cloud Infrastructure Logging service is a highly scalable and fully managed single pane of glass for all the logs in your tenancy. Logging provides access to logs from Oracle Cloud Infrastructure resources
- [OCI Object Storage](https://www.oracle.com/cloud/storage/object-storage/)
    - Oracle Cloud Infrastructure (OCI) Object Storage provides scalable, durable, low-cost storage for any type of data. Benefit from 11 nines of durability. Scale storage to nearly unlimited capacity for your unstructured data
- [Oracle](https://www.oracle.com/)
    - Oracle Website

## License

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 
