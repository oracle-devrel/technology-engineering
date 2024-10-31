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

# A Java AI featured function with local dev and then building and deploying to OCI Functions

Reviewed: 31.10.2024
 
# When to use this asset?
 
Anyone who wants to develop OCI GenAI capable Functions and this example shows how I'm doing this locally using Fn (<a href="https://fnproject.io">https://fnproject.io</a>) on my mac with Apple silicon that uses mainly ARM architecture and then building and then deploying the same to Functions in OCI.

# Author
<a href="https://github.com/mikarinneoracle">mikarinneoracle</a>

# How to use this asset?

This example is based on the <a href="../java-helloworld-with-local-dev-and-oci-functions">java-helloworld-with-local-dev-and-oci-functions</a> and hence building and deploying is exactly the same but this time uses <code>OCI SDK</code> and <code>OCI Generative AI services</code> to produce the function output instead of just a simple "Hello World".

<p>

To do the OCI SDK authentication and authorization to use the GenAI services the function uses two options:
<ul>
<li><b>IAM regular user</b> for the local dev and test on mac</li>
<li><b>InstancePrincipal</b> for the OCI Function by passing config key <code>AUTH_INSTANCE_PRINCIPAL</code> with any value (then not being null)</li>
</ul>

<p>
IAM user option will work on both cases above, as local and as OCI Function.

## Build and test

Before following the steps of the <a href="../java-helloworld-with-local-dev-and-oci-functions">Hello function example </a> adjust the <a href="https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/functions/java-helloworld-AI-with-local-dev-and-oci-functions/files/src/main/java/com/example/HelloAIFunction.java#L93">line 93</a> to match your <code>GenAI service OCID</code>. 

<p>

Testing with curl (or copy-pasting the API Gateway deployment url to a browser):

<p>

<pre>
curl https://n3yu.....ghhi.apigateway.eu-frankfurt-1.oci.customer-oci.com/
What happened today 06/13/2024 100 years ago ?

June 13, 2024 is June 13, 1924. Here are some events that occurred on this date:

1. The German airline Deutsche Lufthansa (DL) was officially founded on June 13, 1924. It is Germany's largest airline and is one of the world's largest airlines in terms of overall passengers carried.
 
2. The British Broadcasting Corporation (BBC) aired its first radio broadcast. 

3. The Hollywood Sign was officially dedicated in California, marking the beginning of Hollywood's rise to prominence in the American film industry. 

4. The Ford Motor Company introduced the firstassembly line to mass produce cars, making cars more accessible to the general public. 

5. The German aerospace company Zeppelin began constructing the Hindenburg, a large passenger airship.
</pre>

# Useful Links
 
- [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
    - Learn how the Functions service lets you create, run, and scale business logic without managing any infrastructure
- [OCI SDK for Java](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdk.htm)
    - The Oracle Cloud Infrastructure SDK for Java enables you to write code to manage Oracle Cloud Infrastructure resources
- [Fn](https://fnproject.io/)
    - The Fn project is an open-source container-native serverless platform that you can run anywhere -- any cloud or on-premise. It’s easy to use, supports every programming language, and is extensible and performant
- [OCI GenAI](https://www.oracle.com/artificial-intelligence/generative-ai/generative-ai-service/)
    - Discover the power of generative AI models equipped with advanced language comprehension for building the next generation of enterprise applications. Oracle Cloud Infrastructure (OCI) Generative AI is a fully managed service for seamlessly integrating these versatile language models into a wide range of use cases, including writing assistance, summarization, analysis, and chat
- [Oracle](https://www.oracle.com/)
    - Oracle Website

## License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 