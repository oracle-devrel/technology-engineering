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

# OCI Container Instances NGINX example 
## With multiple volumes and a custom sidecar to tail access log to OCI Logging and mount the filesystem from OCI Object Storage bucket  

Reviewed: 9.10.2025
 
## When to use this asset?
 
Anyone who wants to experiment with OCI Container Instances and setup a multi-container instance with multiple volumes. In this example I'm using volumes to:
<ul>
    <li>Mount the NGINX filesystem for html data from OCI Object Storage bucket</li>
    <li>Tail NGINX access log to OCI Logging for monitoring</li>
</ul>
These operations will be handled by a custom container that is being built in this example.<br>
The NGINX container is the latest one from Docker Hub without modifications.<br>
The sidecar container is built using <code>OCI SDK</code> in NodeJS, but this could be done also in an other language like Java, Go, Python or .net.

## Author
<a href="https://github.com/mikarinneoracle">mikarinneoracle</a>

## How to use this asset?

First, the sidecar container is built from the <code>source</code> in this repo. This can be done in OCI tenancy Cloud Shell.<br>
Once built it is pushed to OCI Registry (OCIR) repo for deployment as part of the to Container Instances (CI) deployment.
<p>
Then, the CI deployment is created in OCI Resource Manager (RM) from the <code>terraform</code> in this repo.
<p>
However, before creating the RM terraform Stack a few other OCI resources need to be created for the CI deployment:
<ul>
    <li>Object Storage (OS) bucket for the NGINX filesystem. The example content is under <code>www-data</code> in this repo. The NGINX container custom sidecar will mount these files to NGINX <code>/usr/share/nginx/html</code> volume directory</li>
    <li>OCI Logging target for the container sidecar to send the <code>access.log</code> with <code>tail</code> to</li>
</ul>
Once these are created, the RM stack can be created with a configuration that incudes these above among other variables and be deployed.<br>
The result will be a working NGINX with html content from OS and access logs being to OCI Logging for monitoring.

## Steps to complete

### Create OCIR repo

In your OCI tenancy open Cloud UI.
<p>
Create a new repo <code>nginx-sidecar</code> to your home compartment. Keep it as private repo (the default setting).

### Create the sidecar container from source in Cloud Shell

#### Copy source from this repo

In your OCI tenancy open Cloud shell. 
<p>
In cloud shell create subdir for the sidecar container with <code>mkdir nginx-sidecar</code> and cd to it.
<br>
Create the 3 files in <code>source</code> directory. There are several ways to do this but probably easiest is to just a <code>nano</code> editor and copy-paste file contents and save.
<br>
Other ways are to use the file upload from the cloud shell menu after cloning this repo to your localhost and using the Code Editor in the Cloud UI. Choose the one which suits you the best.
<br>

#### Setup OCI SDK Authentication

Since the sidecar container uses OCI SDk to use other OCI services in tenancy we need authenticate and authorize it for the use.
<p>
Normally with any SDK code that runs inside OCI we use use either <code>instance-principal</code> or <code>resource-principal</code> for this purpose depending on the case. Anything that runs on a Virtual Machine (VM) uses <code>instance-principal</code> and services like OCI Functions and Container Instances like in this case use <code>resource-principal</code>. See <a href="https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm">https://docs.oracle.com/en-us/iaas/Content/API/Concepts/sdk_authentication_methods.htm</a> for more info.
<p>
To make testing this example slightly easier let's use your IAM user instead. To do this we package your OCI CLI config into the container image. But be aware not to distribute the container outside your OCI tenancy since it contains your tenancy <code>API KEY</code>.
<p>
To do this create OCI config with OCI CLI in your localhost with <code>oci setup config</code> and copy the created config to your directory in cloud shell. After adding the created API KEY to your profile in OCI tenancy copy the created private key file to your directory in cloud shell, too. Modify the config with nano editor to remove the path from the keyfile e.g.
<pre>key_file = oci_api_key.pem</pre>

#### Build and push to OCIR

After adding the CLI config and API Key build the container and push it to OCIR repo:

<pre>
export ns=$(oci os ns get | jq .data | tr -d '"')
docker build . -t "fra.ocir.io/$ns/nginx-sidecar:1"
docker push  "fra.ocir.io/$ns/nginx-sidecar:1"
</pre>

As always you can change the <code>region</code> to match yours, I'm using the <i>EU-frankurt-1</i> region in this case.

### Create Object Storage bucket with html in www-data

### Create OCI Logging Log target

### Create Resource Manager Stack from terraform files

### Run the the RM Stack to create the CI deployment and test NGINX
