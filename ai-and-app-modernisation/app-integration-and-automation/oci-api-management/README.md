# OCI API Management

Oracle Cloud Infrastructure (OCI) provides a comprehensive set of services to manage the lifecycle of APIs.

**Oracle API Gateway** is a highly available virtual network appliance that can receive API calls at scale and route them to back-end services, such as Serverless Functions, services running on Oracle Kubernetes Engine, Oracle Integration, ORDS and more.

Developers can choose from a wide range of tools to create API descriptions in OpenAPI format which is supported by OCI API Gateway.

API Gateway provides policy enforcement such as limiting the number of requests sent to back-end services, enabling CORS, providing authentication and authorization, adding mTLS support, modifying incoming requests and outgoing responses, cache responses to improve performance and reduce load on back-end services.

API managers can create Usage Plans within API Gateway and define API access tiers. API teams can monitor the traffic and analytics of their APIs based on the usage plan and subscriptions. This enables customers to analyze usage patterns as well as unlock new revenue streams by monetizing APIs.

Review Date: 03.11.2023


# Useful Links

- [Quick Start Guide](https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayquickstartsetupcreatedeploy.htm)
- YouTube Videos
  - [API Gateway Overview by Product Management](https://youtu.be/10U6kTh_0Lc)
  - [Hands-on lab - how to create an API Gateway](https://youtu.be/hES55nIQH0Y)
- [Articles](https://blogs.oracle.com/author/robert-wunderlich) by Product Management
- [Terraform examples](https://github.com/oracle/terraform-provider-oci/tree/master/examples/api_gateway)
- Oracle Functions Samples – API Gateway Authorizer Functions
  - https://github.com/oracle-samples/oracle-functions-samples → See section Functions and API Gateway
  - https://github.com/oracle-samples/sample.fusion-ords-identityprop
- [Oracle Architecture Center](https://docs.oracle.com/solutions/?q=&cType=reference-architectures&product=API%20Gateway&sort=date-desc&lang=en)
  - Reference Architectures with API Gateway

## General Product Links

- [API Management Product Page](https://www.oracle.com/cloud/cloud-native/api-management/)
- [API Gateway Documentation](https://docs.oracle.com/iaas/Content/APIGateway/home.htm)

# Team Publications

Reusable assets can be found in subfolders:
- [fn-authorizer-apigw-oic](fn-authorizer-apigw-oic)
  - Example authorizer function for API Gateway with OIC backend. 
- [fn-authorizer-apigw-ords](fn-authorizer-apigw-ords)
  - Example authorizer function for API Gateway with ORDS backend.
- [oic-with-oci-api-gtw](oic-with-oci-api-gtw)
  - Architecture pattern for exposing APIs deployed in OIC using OCI API Gateway
- [Shared Assets](https://github.com/oracle-devrel/technology-engineering/tree/main/ai-and-app-modernisation/app-integration-and-automation/shared-assets)
  - List of reusable assets spanning multiple cloud services (OIC, OPA, API Gateway)

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
