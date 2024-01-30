# Extend Access WebService

This asset contains the code and deployment items for a RESTful service which will extend user access rights.

The scheduled task needs to be used in conjunction with the Access Extension Notification scheduled task, which will generate the data and send the required actionable notification links. The endpoints exposed by this WebService will act as backend providers for those links.

Developed on and compatible with OIG 11g R2 PS3 and above.

Review Date: 13.11.2023

# When to use this asset?

When there's a need to provide or demonstrate the functionality described above or something similar, which can be adapted from the provided code.

# How to use this asset?

## Pre-requisites and dependencies

The WebService is build using the JAX-RS specification and API.

As such, the following jar files are required as dependencies and need to be used during the build process:
- axis.jar
- commons-discovery-0.2.jar
- commons-logging.jar
- eclipselink.jar
- jackson-core-asl-1.9.2.jar
- jackson-jaxrs-1.9.2.jar
- jackson-mapper-asl-1.9.2.jar
- jackson-xc-1.9.2.jar
- jaxrpc.jar
- jersey-client-1.19.1.jar
- jersey-core-1.19.1.jar
- jersey-json-1.19.1.jar
- jersey-server-1.19.1.jar
- jersey-servlet-1.19.1.jar
- jettison-1.1.jar
- jsr311-api-1.1.1.jar
- saaj.jar
- spring.jar
- wsdl4j.jar

To connect to an OIM node, the service will also use a full OIM client, and will also need the following jar file:
- oimclient.jar

Note that this is a full OIM client. On more details about exporting a full OIM client jar file, please consult the developer's guide linked below.

## Building and deployment

A complete WebContent deployment configuration is provided as a sample, please use it and extend it as needed.

Note that the use of a build system such as Ant or Maven is encouraged, however manually building the war file is also possible, by running `jar -cvf extend_access.war .` in the WebContent folder.

Here's a short build and deployment checklist:

1. Set the proper configuration parameters in the `extendaccessws.properties` file and copy it under `$DOMAIN_HOME/config` on the target WebLogic domain
2. Copy the above mentioned dependency jars under `WebContent\WEB-INF\lib` and build/export the WebService war file.
3. Deploy the war file on a WebLogic node. Note that the deployment node needs to include a deployment of the jdbc/operationsDB datasource, also known as oimOperationsDB. This datasource is typically deployed only on the OIM and SOA nodes of a WebLogic cluster.
4. Activate the new deployment to start servicing requests, if this isn't done automatically.

Please see the useful link below for detailed build and deployment steps.

# Useful Links

[The Java API for RESTful Web Services (JAX-RS)](https://www.oracle.com/technical-resources/articles/java/jax-rs.html)
[JSR 311: JAX-RS: The JavaTM API for RESTful Web Services](https://jcp.org/en/jsr/detail?id=311)
[Oracle Identity Governance developer's guide - Developing scheduled tasks](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/developing-scheduled-tasks.html#GUID-F62EF833-1E70-41FC-9DCC-C1EAB407D151)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
