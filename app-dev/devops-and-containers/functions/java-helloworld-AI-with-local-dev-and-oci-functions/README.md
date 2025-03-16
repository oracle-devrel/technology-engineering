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

To do the OCI SDK authentication and authorization to use the GenAI services the function has three options:
<ul>
<li><b>ResourcePrincipal</b> for the OCI Function to run in OCI. This allows Function to be authorized as part of
a OCI Dynamic Group that has OCI Policies attached to for the Function to do it's job.</li>
<li><b>IAM regular user</b> for the local dev and test on mac and passing the vars in source code (lines 79-84 in HelloAIFunction.java). This works for testing locally but the container should not be distributed!</li>
<li><b>IAM regular user</b> for the local dev and test on mac using OCI CLI config file (usually located in ~/.oci). Again, this works for testing locally but the container should not be distributed!</li>
</ul>

<p>
IAM user option will work on both cases above, as local and as OCI Function. ResourcePrincipal is the default for OCI Function.
<p>

## Build and test

Following the steps of the <a href="../java-helloworld-with-local-dev-and-oci-functions">Hello function example </a> adjust the  <a href="https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/functions/java-helloworld-AI-with-local-dev-and-oci-functions/files/src/main/java/com/example/HelloAIFunction.java#76">line 76</a> to match your <code>compartment OCID</code> and the <a href="https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/functions/java-helloworld-AI-with-local-dev-and-oci-functions/files/src/main/java/com/example/HelloAIFunction.java#77">line 77</a> to match your <code>GenAI service model OCID</code>. 

<p>

To use <code>.oci config</code> for testing locally replace the contents of Dockerfile with the contents from <a href="Dockerfile.local_oci">Dockerfile.local_oci</a>. Then copy your <code>~/.oci</code> -directory under the project root and build the Function with Fn:

<pre>
fn --verbose deploy --app hellofunction --local
fn invoke hellofunction helloaifunc
</pre>

<i>Note! Do not distribute this container since it contains your OCI credentials. Use this only for local testing purposes.</i>

<p>

Testing with curl (or copy-pasting the API Gateway deployment url to a browser):

<p>

<pre>
curl https://n3yu.....ghhi.apigateway.eu-frankfurt-1.oci.customer-oci.com/

What happened at 1925-02-07 ?

On February 7, 1925, several significant events took place around the world:

- In the United States, the Grand Ole Opry, a famous country music stage and radio show, made its debut on WSM radio in Nashville, Tennessee. It was initially called the "WSM Barn Dance" and has since become one of the longest-running radio programs in history.

- The first issue of "The New Yorker" magazine was published in New York City. Founded by Harold Ross, the magazine quickly gained a reputation for its sophisticated and witty writing, featuring contributions from renowned writers and artists.

- In the field of aviation, the first non-stop flight from England to India was completed by Squadron Leader John Henry "Jack" Moore-Brabazon, 1st Baron Brabazon of Tara. He flew a modified Airco DH.9A biplane, covering a distance of approximately 4,130 miles (6,646 kilometers) in about 50 hours and 37 minutes.

- In sports, the 1925 Rose Bowl game was played in Pasadena, California. The game, which is an annual college football bowl game, saw the Dartmouth Indians defeat the California Golden Bears by a score of 14-0.

- In the world of literature, the novel "The Great Gatsby" by F. Scott Fitzgerald was published in the United States. The book, set in the 1920s, explores themes of social class, wealth, and the American Dream, and has since become a classic of American literature.

- In the realm of science, the American chemist Wallace Carothers filed a patent for the synthetic polymer nylon. Nylon, known for its strength and versatility, would go on to revolutionize the textile industry and find applications in various products.

- In Europe, the Locarno Treaties were signed in Switzerland. These treaties aimed to promote peace and security in Europe after World War I. They included mutual guarantees of borders and commitments to resolve disputes peacefully.

These are just a few notable events that occurred on February 7, 1925. The day witnessed advancements in entertainment, aviation, sports, literature, science, and international diplomacy.
</pre>

# Native image using GraalVM

GraalVM compiles your Java functions ahead of time into standalone binaries that start instantly, provide peak performance with no warmup, and use fewer resources. The key GraalVM benefits are: Low Resource Usage: Java applications compiled ahead-of-time by GraalVM require less memory and CPU to run.

<p>

To do this <a href="https://github.com/oracle-devrel/technology-engineering/tree/main/app-dev/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm">create OCI DevOps project for a Function CI/CD</a> and then clone the repo and copy the following files with the Function <a href="./files/src/">source</a> and commit and push them to the repo:
<p>
<ul>
    <li><a href="./files/Dockerfile.native">Dockerfile.native</a></li>
    <li><a href="./files/build_spec_native.yaml">build_spec_native.yaml</a></li>
    <li><a href="./files/reflection.json">reflection.json</a></li>
    <li><a href="./files/pom.xml">pom.xml</a></li>
</ul>

<p>
After pushing run the native build pipeline and <a href="https://github.com/oracle-devrel/technology-engineering/blob/main/app-dev/devops-and-containers/devops/oci-devops-terraform-function-java-graalvm/README.md#testing">test the Function in cloud shell</a>.
<p>


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