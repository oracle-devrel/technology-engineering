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

# OCI Container Instances NGINX example with multiple volumes and a custom sidecar to tail access log to OCI Logging and mount the filesystem from OCI Object Storage bucket  

Reviewed: 9.10.2025
 
# When to use this asset?
 
Anyone who wants to experiment with OCI Container Instances and setup a multi-container instance with multiple volumes. In this example I'm using volumes to:
<ul>
    <li>Mount the NGINX filesystem for html data from OCI Object Storage bucket</li>
    <li>Tail NGINX access log to OCI Logging for monitoring</li>
</ul>
These operations will be handled by a custom container that is being built in this example.<br>
The NGINX container is the latest one from Docker Hub without modifications.<br>
The sidecar container is built using <code>OCI SDK</code> in NodeJS, but this could be done also in an other language like Java, Go, Python or .net.

# Author
<a href="https://github.com/mikarinneoracle">mikarinneoracle</a>

# How to use this asset?

First, the sidecar container is built from the <code>source</code> in this repo. This can be done in OCI tenancy Cloud Shell.<br>
Once built it is pushed to OCI Registry (OCIR) repo for deployment to Container Instances (CI) as part of the CI deployment.
<p>
Then, the CI deployment is created in OCI Resource Manager (RM) from the <code>terraform</code> in this repo.
<p>
However, before creating the RM terraform Stack a few other OCI resources need to be created for the CI deployment:
<ul>
    <li>Object Storage (OS) bucket for the NGINX filesystem. The example content is under <code>www-data</code> in this repo. Container sider will mount these files the NGINX <code></code>/usr/share/nginx/html</code> volume directory</li>
    <li>OCI Logging target for the container sidecar to send the <code>access.log with tail</code> to</li>
</ul>
Once these are created, the RM stack can be created with a configuration that incudes these above among other variables and deployed.<br>
The result will be a working NGINX with html content from OS and access logs being to OCI Logging for monitoring.



