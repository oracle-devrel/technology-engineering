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

## Functions overview
[Document functions-overview](files/Fn.pdf)

### Author
<a href="https://github.com/mikarinneoracle">mikarinneoracle</a>

# A Java Hello World function with local dev and then building and deploying to OCI Functions

This is an example how I'm locally developing and testing OCI Functions on my mac with Apple silicon that uses mainly ARM architecture and then building and deploying the same to Functions in OCI.

<p>

I've installed maven and <code>Fn cli</code> on my mac. This is how to do the <a href="https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsinstallfncli.htm">Fn cli install</a> or like in here <a href="https://fnproject.io/tutorials/install/">following the Fn tutorial</a>. 

<p>

To develop functions locally I'm running the Fn server; to do this I'm using this command with Rancher Desktop instead of doing the usual <code>fn start</code> that works for me:

<pre>
docker run --rm -i --name fnserver \
-v /tmp/iofs:/iofs \
-e FN_IOFS_DOCKER_PATH=/tmp/iofs \
-e FN_IOFS_PATH=/iofs \
-v /tmp/data:/app/data \
-v /var/run/docker.sock:/var/run/docker.sock \
--privileged \
-p 8080:8080 \
--entrypoint ./fnserver \
-e FN_LOG_LEVEL=DEBUG fnproject/fnserver:latest
</pre>

<p>
Now that the Fn server is running create an application for our function using the cli:

<pre>
fn create app hellofunction
</pre>

<p>

Then clone this repo and project and cd to the project root directory. Then run Fn cli command to build and deploy the function locally:

<pre>
fn --verbose deploy --app hellofunction --local
</pre>

<p>

After this you are ready to call the function to test it:

<pre>
fn invoke hellofunction hellofunc
Hello, world!
</pre>

or

<pre>
echo 'Mika' | fn invoke hellofunction hellofunc
Hello, Mika!
</pre>

<p>

Now that the function is properly working locally let's build and deploy it to OCI.

<p>

First create a OCIR repo for the container in your OCI tenancy <code>compartment</code> you want push the container into. Unless you do this first the container will be pushed to the <code>root</code> comaprtment that is not a good idea and will usually lead to 404 or 502 errors when the OCI Function pulling the container due to missing OCI policies. You can create the OCIR repo from the Cloud UI or using the <a href="https://docs.oracle.com/en-us/iaas/tools/oci-cli/3.41.0/oci_cli_docs/cmdref/artifacts/container/repository/create.html">oci cli</a>.

<p>


