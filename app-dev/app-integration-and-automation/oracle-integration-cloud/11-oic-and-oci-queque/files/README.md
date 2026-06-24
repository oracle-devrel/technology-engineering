# Project OCI-queue-demo

## Why use this solution 

This project provides solutions for automating message processing and queue management, benefiting industries such as cloud, financial, and technology, by enabling real-time data processing, efficient queue management, and event-driven business object processing.

# Overview 

The project orchestrates publishing and consuming messages from OCI queues, triggering transformations, mappings, and events, leveraging REST APIs and scheduled orchestration to facilitate event-driven business object processing and queue management.

## View general details 

### Name: OCI-queue-demo
### Identifier: OCI_QUEUE_DEMO
### Keywords: oci queue
### Description: OCI queuing

## Applications and access 

You need this applications and access data to activate and run this solution.

- *OCI-Queues*

        *Security Policy:* Oci Service Invocation

        *Security Properties:* dummy_credential_rpst
- *MyAPITrigger*

        *Security Policy:* Multi Token Inbound

## Integrations
### Event_OCI_Queue_Consume - v01.00.0000

The integration flow consumes messages from an OCI queue, processes them, and then deletes the messages from the queue, likely in an enterprise or cloud-based setting, working with event-driven business objects. The orchestration flow appears to be designed for event-driven message processing and queue management, possibly in industries that rely heavily on real-time data processing and integration.

### OCI_Queue_Publisher - v01.00.0000

The integration flow publishes a message to an OCI queue, triggering a series of transformations and mappings to process the message. The orchestration flow likely targets the technology or cloud industry, working with business objects such as messages, queues, and APIs to achieve the desired outcome.

### OCI_Queue_Publisher_risingEvent - v01.00.0000

The integration flow triggers a message to be published to an OCI queue, and then checks the queue, potentially targeting the technology or cloud computing industry, and likely working with message or event business objects. The orchestration flow ultimately results in publishing a business event, such as a check queue event, after processing and transforming the message.

### ConsumeQueueScheduler - v01.00.0000

The integration flow automates the consumption of messages from a queue, triggering a series of actions to process and transform the data, ultimately leading to the rise of an event to consume from a specific queue. The orchestration flow likely targets the financial industry, working with business objects such as queue messages and event triggers.

## Deployments

**Name: OCI-queue-demo-projectAll
Description: OCI-queue-demo-projectAll**

## Regenerate Review testing suggestions
To activate, run, and monitor the project, start by triggering each integration individually, then test the entire flow from start to end. 

Use the Oracle Integration user interface to track the flow of messages and debug any issues. Begin by triggering the OCI Queue Publisher integration, then verify that the message is consumed by the Consume Queue Scheduler integration, and finally check that the Event OCI Queue Consume integration processes and deletes the message from the queue. Monitor the flow using the Tracking page and verify that each integration completes successfully.

