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

During following the steps of the <a href="../java-helloworld-with-local-dev-and-oci-functions">Hello function example </a> adjust the <a href="https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/functions/java-helloworld-AI-with-local-dev-and-oci-functions/files/src/main/java/com/example/HelloAIFunction.java#L93">line 93</a> to match your <code>GenAI service OCID</code>. 

<p>

Testing with curl (or copy-pasting the API Gateway deployment url to a browser):

<p>

<pre>
curl https://n3yu.....ghhi.apigateway.eu-frankfurt-1.oci.customer-oci.com/

What happened today 01/17/2025 100 years ago ?
On January 17th, 1925, 100 years ago, the following events took place:
- In the US, President Calvin Coolidge delivered his annual State of the Union address to Congress. He discussed the thriving state of the national economy, emphasizing the record-high production of American industries and the growth of the country's merchant marine fleet. Coolidge also urged Congress to pass legislation facilitating world trade and improving diplomatic relations.
- The first Winter Sports Week was held in Chamonix, France. This event eventually evolved into the prestigious Chamonix International Festival of Sports and Cinema.
- The play "The New York Idea" by Langdon Mitchell premiered at the Ambassador Theatre on Broadway. It ran for 144 performances and received critical acclaim.
- The silent film "The Gold Rush" directed by Charlie Chaplin was released in the United States. It's a classic comedy that tells the story of a prospector during the Klondike Gold Rush. Chaplin's unique brand of physical comedy and the film's innovative effects delighted audiences.
- In Germany, the Weimar Republic experienced a political scandal known as the "German-Russian Trade and Credit Agreement." The agreement, which granted Germany a loan of 300 million marks from Russia, was signed secretly, leading to accusations of mismanagement and lack of transparency in the government. This incident further destabilized the already fragile Weimar Republic.
</pre>

# Native image using GraalVM

GraalVM compiles your Java functions ahead of time into standalone binaries that start instantly, provide peak performance with no warmup, and use fewer resources. The key GraalVM benefits are: Low Resource Usage: Java applications compiled ahead-of-time by GraalVM require less memory and CPU to run.

<p>

To do this a Docker multi-stage build is used.

<p>

Before building the native image let's do a full maven build for the project to create the necessary libraries under <code>target/lib</code>:

<pre>
mvn clean install
</pre>

Then build the Docker container using <a href="./files/Dockerfile.native">multi-stage Docker file</a> including the GraalVM native image compilation:

<pre>
docker build -f Dockerfile.native -t fra.ocir.io/&lt;YOUR OCI TENANCY NAMESPACE&gt;/helloworldai-java:2 .
</pre>

The GraalVM compilation stage requires quite a bit resources from your localhost so in case for example using Rancher desktop
think of increasing the CPU and memory for it to make the build faster.

<p>

In the <a href="./files/Dockerfile.native">Dockerfile.native</a> two things are important: Including the <a href="./files/reflection.json">reflection.json</a> with the proper function class name and passing Fn FDK libraries with <code>"-Djava.library.path=/lib"</code> in the container CMD along with the <code>"com.example.HelloAIFunction::handleRequest"</code> function handler.

<p>

After the build push the container to OCIR repo:

<pre>
docker push fra.ocir.io/&lt;YOUR OCI TENANCY NAMESPACE&gt;/helloworldai-java:2
</pre>

Finally deploy the container to your OCI Function by replacing the container using the Cloud UI by editing the function and changing the container from <code>helloworldai-java:1</code> to <code>helloworldai-java:2</code>. Then test it.


# Useful Links
 
- [OCI Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Concepts/functionsoverview.htm)
    - Learn how the Functions service lets you create, run, and scale business logic without managing any infrastructure
- [OCI SDK for Java](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/javasdk.htm)
    - The Oracle Cloud Infrastructure SDK for Java enables you to write code to manage Oracle Cloud Infrastructure resources
- [Fn](https://fnproject.io/)
    - The Fn project is an open-source container-native serverless platform that you can run anywhere -- any cloud or on-premise. It’s easy to use, supports every programming language, and is extensible and performant
- [OCI GenAI](https://www.oracle.com/artificial-intelligence/generative-ai/generative-ai-service/)
    - Discover the power of generative AI models equipped with advanced language comprehension for building the next generation of enterprise applications. Oracle Cloud Infrastructure (OCI) Generative AI is a fully managed service for seamlessly integrating these versatile language models into a wide range of use cases, including writing assistance, summarization, analysis, and chat
- [OCI Functions with GraalVM](https://github.com/shaunsmith/graalvm-fn-init-images)
    - Discover GraalVM Native Image -based functions with this example GitHub repo
- [Oracle](https://www.oracle.com/)
    - Oracle Website

## License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](LICENSE) for more details.

ORACLE AND ITS AFFILIATES DO NOT PROVIDE ANY WARRANTY WHATSOEVER, EXPRESS OR IMPLIED, FOR ANY SOFTWARE, MATERIAL OR CONTENT OF ANY KIND CONTAINED OR PRODUCED WITHIN THIS REPOSITORY, AND IN PARTICULAR SPECIFICALLY DISCLAIM ANY AND ALL IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY, AND FITNESS FOR A PARTICULAR PURPOSE.  FURTHERMORE, ORACLE AND ITS AFFILIATES DO NOT REPRESENT THAT ANY CUSTOMARY SECURITY REVIEW HAS BEEN PERFORMED WITH RESPECT TO ANY SOFTWARE, MATERIAL OR CONTENT CONTAINED OR PRODUCED WITHIN THIS REPOSITORY. IN ADDITION, AND WITHOUT LIMITING THE FOREGOING, THIRD PARTIES MAY HAVE POSTED SOFTWARE, MATERIAL OR CONTENT TO THIS REPOSITORY WITHOUT ANY REVIEW. USE AT YOUR OWN RISK. 