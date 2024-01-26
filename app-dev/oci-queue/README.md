<!--
Copyright (c) 2024 Oracle and/or its affiliates.

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

## OCI queue overview
[Document queue-overview](files/queue_overview.pdf)

## OCI Queue example in NodeJS with GitHub Actions

### OCI Queue

Create Queue and copy the Queue <i>OCID</i> and <i>Messages endpoint</i>:

<p>
<img src="files/endpoint.png" width="800" />

<p>
When using another <code>region</code> than <code>EU_FRANKFURT_1</code> please modify the 
<a href="index.js#L48">
<code>index.js</code></a> Line #48 accordingly:

<pre>
const region = common.Region.EU_FRANKFURT_1;
</pre>

### Policies

Setup policies for your user in the tenancy

e.g. <code>Allow &lt;USER_GROUP&gt; to manage queues in compartment &lt;COMPARTMENT&gt;</code>

More on OCI Queue IAM policies: https://docs.oracle.com/en-us/iaas/Content/queue/policy-reference.htm

### Secrets

Setup secrets to run this example with GitHub Actions:

<ul>
    <li><b>OCI_TENANCY</b>: OCI Tenancy OCID</li>
    <li><b>OCI_USER</b>: OCI User OCID</li>
    <li><b>OCI_FINGERPRINT</b>: OCI User Fingerprint</li>
    <li><b>OCI_KEY</b>: OCI User Private Key</li>
    <li><b>OCI_PASSPHRASE</b>: OCI User Private Key passphrase (optional)</li>
    <li><b>Q_ID</b>: OCI Queue OCID</li>
    <li><b>Q_ENDPOINT</b>: OCI Queue Messages endpoint</li>
</ul>

### Run Action

Monitor the GitHub action to run:

<p>
<img src="files/action.png" width="800" />

<p>
This example will poll for messages in the queue and finally writes a new message to it.

### View messages in the Queue

<img src="files/messages.png" width="800" />

### Running locally

Clone this repo, setup npm and <code>oci cli</code> and modify <a href="index.js#L46">index.js</a> line 46 by uncommenting it and removing/commenting lines 49-56 and replace lines 59-60
with Queue details :

<pre>
// Use this locally instead of env vars and region:
const provider = new common.ConfigFileAuthenticationDetailsProvider();

// Q settings
const queueId = 'ocid1.queue.oc1.eu-frankfurt-1.ama....a5z4ic2tslq';
const endpoint = 'https://cell-1.queue......oci.oraclecloud.com';
</pre>

Then run:

<pre>
npm install
node index.js
</pre>

### Sending messages to Queue

You can manually send messages to the queue using the OCI Queue Console  
<code>Actions/Send Message</code> and then see them being received by re-running the build.

<p>
You can also play with the queue's <code>Dead Letter Queue</code> settings to see how many
times the same message is being received (default is 5). To do this comment the 
<a href="index.js#L99">line 99 of the index.js</a> and re-run the build using commit. 
